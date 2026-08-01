-- LifeWeeks: начальная схема.
-- Применяется идемпотентно, безопасно запускать повторно.

CREATE TABLE IF NOT EXISTS users (
    telegram_id     BIGINT PRIMARY KEY,
    birth_date      DATE,
    username        TEXT,
    first_name      TEXT,
    language_code   TEXT,
    timezone        TEXT        NOT NULL DEFAULT 'Europe/Moscow',
    daily_time      TIME        NOT NULL DEFAULT '20:00',
    weekly_time     TIME        NOT NULL DEFAULT '09:00',
    notifications   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ежедневный чек-ин. Одна оценка на пользователя в день, повторная перезаписывает.
CREATE TABLE IF NOT EXISTS daily_checkins (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users (telegram_id) ON DELETE CASCADE,
    day         DATE   NOT NULL,
    rating      TEXT   NOT NULL CHECK (rating IN ('good', 'neutral', 'bad')),
    source      TEXT   NOT NULL DEFAULT 'bot' CHECK (source IN ('bot', 'webapp')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, day)
);

-- Главный индекс под выборку "чек-ины пользователя за диапазон дат".
CREATE INDEX IF NOT EXISTS daily_checkins_user_day_idx
    ON daily_checkins (user_id, day DESC);

-- Недельная оценка — совместимость со старым фронтом (endpoint /rate-week).
CREATE TABLE IF NOT EXISTS week_ratings (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users (telegram_id) ON DELETE CASCADE,
    week_start  DATE   NOT NULL,
    rating      TEXT   NOT NULL CHECK (rating IN ('good', 'neutral', 'bad')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, week_start)
);

CREATE INDEX IF NOT EXISTS week_ratings_user_week_idx
    ON week_ratings (user_id, week_start DESC);

-- Журнал рассылок: даёт идемпотентность планировщику.
-- Уникальность (user_id, kind, target_date) гарантирует "не более одной
-- рассылки данного типа за день", даже если сервис перезапустился в тик.
CREATE TABLE IF NOT EXISTS notifications_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users (telegram_id) ON DELETE CASCADE,
    kind        TEXT   NOT NULL CHECK (kind IN ('daily', 'weekly')),
    target_date DATE   NOT NULL,
    sent_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, kind, target_date)
);

-- Триггер обновления updated_at.
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['users', 'daily_checkins', 'week_ratings'] LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS %I_set_updated_at ON %I', t, t);
        EXECUTE format(
            'CREATE TRIGGER %I_set_updated_at BEFORE UPDATE ON %I '
            'FOR EACH ROW EXECUTE FUNCTION set_updated_at()', t, t);
    END LOOP;
END;
$$;
