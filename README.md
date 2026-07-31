# petr-ai — landing page

Лендинг студии автоматизации **petr-ai**: Telegram-боты, AI-агенты, n8n-воркфлоу
и интеграции с маркетплейсами.

Стек: Vite + React 18 + TypeScript + Tailwind CSS + Framer Motion + lucide-react.
Тёмная тема, единственный акцент — `#ff8a3d`.

## Команды

```bash
npm install
npm run dev      # локальная разработка на http://localhost:5173
npm run build    # production-сборка в dist/
npm run preview  # предпросмотр собранного dist/
```

`npm run build` даёт полностью статический `dist/` — его можно отдавать любым
статическим хостингом (nginx, GitHub Pages, Netlify, Vercel, S3) без Node на
сервере. Сборка использует `base: './'`, поэтому работает и в подпапке.

## Структура

```
src/
  App.tsx                  порядок секций
  data/site.ts             весь контент: услуги, проекты, ссылка на Telegram
  components/
    Navbar.tsx             плавающая навигация из пилюль
    Hero.tsx               разбросанная типографика + статистика по углам
    Services.tsx           нумерованный список 01–05
    Projects.tsx           контейнер со scroll-прогрессом
    ProjectCard.tsx        sticky-карточка проекта
    Contact.tsx / Footer.tsx
    FadeIn.tsx             обёртка появления по скроллу
    Button.tsx             пилюля-кнопка (solid / accent / outline)
    MagneticButton.tsx     CTA с магнитным hover
    StatBlock.tsx          цифра + подпись + диагональная черта
  hooks/useMediaQuery.ts
public/img/                скриншоты проектов
```

## Картинки проектов

Пути к изображениям лежат в `src/data/site.ts` (поле `image`) и указывают на
файлы в `public/img/`. Чтобы поменять картинку — достаточно положить файл в
`public/img/` и поправить имя в этом массиве.

Восемь скриншотов уже извлечены из старого сайта. Ещё шесть карточек пока
показывают градиентную заглушку — положите файлы с этими именами в `public/img/`,
и они подхватятся автоматически:

| Файл | Проект | Файл на старом сайте |
| --- | --- | --- |
| `interior-fal.png` | Визуализация интерьеров через fal.ai | — |
| `face-swap.png` | Сервис замены лиц на фото | — |
| `beauty-crm.png` | Агент записи + CRM для beauty-студии | `img/4к345к345к.PNG` |
| `ai-realtor.png` | AI Realtor — CRM (Пхукет) | — |
| `smarthome-auditor.png` | SmartHome Security Auditor | `img/sdfdsfggdf.PNG` |
| `moidom.png` | МойДом | `img/tertertg.PNG` |

## Доступность и анимации

Все анимации Framer Motion отключаются при `prefers-reduced-motion: reduce`:
контент сразу отображается в конечном состоянии, амбиентный дрейф точечной
сетки и магнитный hover не запускаются.

Sticky-стек карточек проектов включается с ширины 1024px; ниже карточки
переключаются на одноколоночную вёрстку и скроллятся обычным списком.
