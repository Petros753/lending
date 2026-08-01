#!/usr/bin/env bash
#
# Установка/обновление LifeWeeks на сервере (Ubuntu, root).
# Идемпотентен: повторный запуск обновляет код и перезапускает сервис.
#
#   ./install.sh            # полная установка
#   ./install.sh --update   # только код + рестарт, без БД и nginx
#
set -euo pipefail

APP_DIR=/opt/lifeweeks
WEB_DIR=/var/www/lifeweeks
DB_NAME=lifeweeks
DB_USER=lifeweeks
SERVICE=lifeweeks
NGINX_SITE=lifeweeks.pukikuki.ru

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPDATE_ONLY=false
[[ "${1:-}" == "--update" ]] && UPDATE_ONLY=true

say() { printf '\n\033[1;34m==> %s\033[0m\n' "$1"; }

# ---------------------------------------------------------------- backend
say "Код бэкенда → $APP_DIR/backend"
mkdir -p "$APP_DIR/backend"
rsync -a --delete \
    --exclude '.env' --exclude '__pycache__' --exclude '.pytest_cache' \
    "$REPO_DIR/backend/" "$APP_DIR/backend/"

say "venv и зависимости"
[[ -d "$APP_DIR/venv" ]] || python3.12 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/backend/requirements.txt"

if [[ ! -f "$APP_DIR/backend/.env" ]]; then
    cp "$APP_DIR/backend/.env.example" "$APP_DIR/backend/.env"
    chmod 600 "$APP_DIR/backend/.env"
    echo "!! Создан $APP_DIR/backend/.env — впишите BOT_TOKEN и пароль БД."
fi

# ---------------------------------------------------------------- frontend
say "Mini App → $WEB_DIR"
mkdir -p "$WEB_DIR"
# Без --delete: в каталоге может лежать что-то, положенное руками.
rsync -a "$REPO_DIR/frontend/" "$WEB_DIR/"

if [[ "$UPDATE_ONLY" == false ]]; then
    # ------------------------------------------------------------ database
    say "База данных"
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
        DB_PASS="$(openssl rand -hex 16)"
        sudo -u postgres psql -c "CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASS'"
        echo "!! Роль $DB_USER создана. Строка подключения для .env:"
        echo "   DATABASE_URL=postgresql://$DB_USER:$DB_PASS@127.0.0.1:5432/$DB_NAME"
    else
        echo "Роль $DB_USER уже есть — пароль не трогаем."
    fi
    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
        sudo -u postgres createdb -O "$DB_USER" "$DB_NAME"
    fi
    # Схему накатывает сам сервис при старте (app/db.py: run_migrations).

    # ------------------------------------------------------------- nginx
    say "nginx"
    cp "$REPO_DIR/deploy/nginx/$NGINX_SITE.conf" "/etc/nginx/sites-available/$NGINX_SITE"
    # Старые конфиги на тот же домен: их одновременное включение и было
    # причиной путаницы, какой из них применяется.
    rm -f /etc/nginx/sites-enabled/lifeweeks
    rm -f "/etc/nginx/sites-enabled/$NGINX_SITE"
    ln -s "/etc/nginx/sites-available/$NGINX_SITE" "/etc/nginx/sites-enabled/$NGINX_SITE"
    nginx -t
    systemctl reload nginx

    # ------------------------------------------------------------ systemd
    say "systemd"
    cp "$REPO_DIR/deploy/$SERVICE.service" "/etc/systemd/system/$SERVICE.service"
    systemctl daemon-reload
    systemctl enable "$SERVICE"
fi

say "Перезапуск $SERVICE"
systemctl restart "$SERVICE"
sleep 2
systemctl --no-pager --lines=15 status "$SERVICE" || true

say "Проверка"
curl -fsS http://127.0.0.1:5678/health && echo
echo "Готово. Логи: journalctl -u $SERVICE -f"
