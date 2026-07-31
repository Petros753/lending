export const TELEGRAM_URL = 'https://t.me/Automatizacion007'

export type Service = {
  number: string
  title: string
  description: string
  tags: string[]
}

export const services: Service[] = [
  {
    number: '01',
    title: 'Интеграция сервисов',
    description:
      'Связываю CRM, мессенджеры, маркетплейсы и другие сервисы в единую экосистему',
    tags: ['Bitrix24', 'ELMA365', 'amoCRM'],
  },
  {
    number: '02',
    title: 'AI-автоматизация',
    description:
      'Внедряю нейросети в бизнес-процессы: генерация контента, анализ данных, чат-боты',
    tags: ['Claude API', 'OpenAI', 'fal.ai'],
  },
  {
    number: '03',
    title: 'Telegram-боты',
    description:
      'Разрабатываю ботов для бизнеса с интеграцией в CRM, системы бронирования и аналитику',
    tags: ['Bot API', 'Userbot', 'MTProto'],
  },
  {
    number: '04',
    title: 'Telegram Mini Apps',
    description:
      'Разрабатываю полноценные веб-приложения внутри Telegram: каталоги, магазины, личные кабинеты, формы заявок — с автоматизацией на бэкенде через n8n',
    tags: ['Mini App', 'WebApp API', 'n8n'],
  },
  {
    number: '05',
    title: 'Маркетплейсы',
    description:
      'Автоматизирую работу с Wildberries, Ozon, Яндекс.Маркет: перенос товаров, синхронизация',
    tags: ['Wildberries', 'Ozon', 'Avito'],
  },
]

export type Project = {
  /** Category label shown above the title. */
  category: string
  title: string
  description: string
  /** Optional highlighted result sentence, rendered in the accent colour. */
  highlight?: string
  stack: string[]
  /**
   * Path to the project screenshot, served from `public/img/`. Kept relative to
   * the deploy base — swap the filename here to change the image, nothing else
   * references it. Cards whose file is missing fall back to a gradient panel.
   */
  image: string
  imageAlt: string
}

export const projects: Project[] = [
  {
    category: 'AI + Маркетплейсы',
    title: 'Перенос товаров между маркетплейсами с AI-анализом',
    description:
      'Система автоматического переноса каталога товаров между Wildberries, Ozon и Яндекс.Маркет с умным маппингом категорий через Claude API',
    stack: ['n8n', 'Claude API', 'Wildberries API', 'Ozon API'],
    image: 'img/marketplace-transfer.webp',
    imageAlt: 'Перенос товаров между маркетплейсами workflow',
  },
  {
    category: 'Авито',
    title: 'AI-автоответчик для Avito',
    description:
      'Автоматические ответы на сообщения покупателей с учётом контекста объявления и истории переписки',
    stack: ['n8n', 'Avito API', 'OpenAI'],
    image: 'img/avito-autoresponder.webp',
    imageAlt: 'Автоответчик Avito workflow',
  },
  {
    category: 'Продажи',
    title: 'Расшифровка звонков для РОП',
    description:
      'Автоматическая транскрибация звонков менеджеров, AI-анализ качества и отчёты руководителю отдела продаж.',
    highlight: 'Конверсия отдела +18% за 2 месяца.',
    stack: ['n8n', 'Whisper API', 'Claude API', 'Telegram'],
    image: 'img/call-transcription.webp',
    imageAlt: 'Расшифровка звонков workflow',
  },
  {
    category: 'Рекрутинг',
    title: 'HR-автоматизация HeadHunter → ELMA365',
    description:
      'Автоматический сбор откликов, парсинг резюме и создание карточек кандидатов в CRM.',
    highlight: 'Скорость обработки выросла в 4 раза.',
    stack: ['n8n', 'HeadHunter API', 'ELMA365'],
    image: 'img/hr-headhunter-elma.webp',
    imageAlt: 'HR-автоматизация HeadHunter ELMA365 workflow',
  },
  {
    category: 'AI-генерация',
    title: 'Визуализация интерьеров через fal.ai',
    description:
      'Воркфлоу для дизайн-студии: загрузка фото → генерация вариантов интерьера → отправка клиенту',
    stack: ['n8n', 'fal.ai Flux Pro', 'Telegram'],
    image: 'img/interior-fal.png',
    imageAlt: 'Визуализация интерьеров через fal.ai workflow',
  },
  {
    category: 'Контент',
    title: 'RSS-агрегатор новостей недвижимости',
    description:
      'Сбор новостей из 10+ источников, AI-рерайт и публикация в Telegram с модерацией',
    stack: ['n8n', 'RSS', 'Claude API', 'Telegram'],
    image: 'img/rss-realestate.webp',
    imageAlt: 'RSS агрегатор workflow',
  },
  {
    category: 'Документы',
    title: 'Генератор PDF-коммерческих предложений',
    description:
      'Автоматическое создание красивых КП для продажи ЧПУ-оборудования из данных формы',
    stack: ['n8n', 'PDF Generation', 'Webhook'],
    image: 'img/pdf-proposals.webp',
    imageAlt: 'Генератор PDF-коммерческих предложений workflow',
  },
  {
    category: 'Face Swap',
    title: 'Сервис замены лиц на фото',
    description:
      'Telegram-бот для замены лиц с использованием WaveSpeed AI API и системой оплаты',
    stack: ['n8n', 'WaveSpeed AI', 'Telegram Bot'],
    image: 'img/face-swap.png',
    imageAlt: 'Сервис замены лиц на фото workflow',
  },
  {
    category: 'AI + RAG',
    title: 'AI-консультант с RAG‑памятью',
    description:
      'Telegram-бот с долговременной памятью: текст/голос/изображения → поиск по базе знаний (RAG) → точный ответ с контекстом.',
    stack: ['n8n', 'Supabase Vector', 'OpenAI'],
    image: 'img/rag-consultant.png',
    imageAlt: 'AI-консультант с RAG-памятью workflow',
  },
  {
    category: 'Ассистент',
    title: 'Личный AI‑секретарь',
    description:
      'Принимает файлы, фото и голосовые, анализирует и отвечает, ведёт диалог с памятью и может работать с календарём/почтой через инструменты.',
    highlight: 'Экономит 2+ часа в день.',
    stack: ['Telegram', 'OpenAI', 'n8n'],
    image: 'img/ai-secretary.png',
    imageAlt: 'Личный AI-секретарь workflow',
  },
  {
    category: 'AI-агент + CRM',
    title: 'Агент записи + CRM для beauty-студии',
    description:
      'Telegram-агент на n8n с RAG на Supabase Vector Store и памятью в PostgreSQL: голосовой ввод через Whisper, проверка свободных слотов из базы клиентов и бронирование прямо в чате. Плюс кастомная CRM на React + PostgREST — записи, мастера, услуги, расходы и дашборд с KPI.',
    highlight: 'Всё под контролем клиента, без внешних SaaS.',
    stack: [
      'n8n',
      'Supabase Vector',
      'Whisper',
      'PostgreSQL',
      'React',
      'PostgREST',
      'OpenAI',
    ],
    // original site file: img/4к345к345к.PNG
    image: 'img/beauty-crm.png',
    imageAlt: 'CRM дашборд beauty-студии',
  },
  {
    category: 'CRM + Mini App',
    title: 'AI Realtor — CRM для агентства недвижимости (Пхукет)',
    description:
      'CRM для рынка новостроек Пхукета: админ-панель на React + FastAPI + PostgreSQL — каталог ЖК → корпуса → квартиры → медиа и прайс-листы, роли и права, аналитика продаж, учёт наличия и интеграция с Google Drive. Для агентов — Telegram Mini App с поиском по фильтрам и формированием КП в один клик.',
    stack: [
      'React',
      'FastAPI',
      'PostgreSQL',
      'Telegram Mini App',
      'Google Drive API',
    ],
    image: 'img/ai-realtor.png',
    imageAlt: 'AI Realtor CRM для агентства недвижимости',
  },
  {
    category: 'Open Source · Security',
    title: 'SmartHome Security Auditor',
    description:
      'Собственный open-source CLI (MIT) для аудита безопасности умного дома: находит IoT-устройства в сети и прогоняет 40+ проверок — дефолтные пароли, HTTP/SSL, telnet/SSH, UPnP, CORS, известные CVE. Home Assistant, Tuya, Xiaomi, Zigbee, MQTT. Отчёты в HTML/JSON/консоль, Telegram-алерты на critical.',
    highlight: 'Python 3.11 + async — системная экспертиза за пределами n8n.',
    stack: ['Python', 'async · aiohttp', 'IoT Security', 'SQLite', 'MIT'],
    // original site file: img/sdfdsfggdf.PNG
    image: 'img/smarthome-auditor.png',
    imageAlt: 'SmartHome Security Auditor',
  },
  {
    category: 'Mobile App + SaaS',
    title: 'МойДом — нативное приложение для управляющих компаний',
    description:
      'Полноценное мобильное приложение для жильцов (не бот и не мини-апп): заявки в УК с фото, показания счётчиков, объявления, чат на WebSocket, push-уведомления. React Native / Expo, сборка APK через EAS. Бэкенд на Bun + Hono + PostgreSQL/Prisma + Redis, JWT + Firebase Phone Auth, мультитенантная архитектура. Плюс админ-панель для УК.',
    highlight: 'Домофон и камеры — в роадмапе.',
    stack: [
      'React Native',
      'Expo',
      'Bun',
      'Hono',
      'PostgreSQL',
      'Prisma',
      'Redis',
      'WebSocket',
      'Firebase Auth',
    ],
    // original site file: img/tertertg.PNG
    image: 'img/moidom.png',
    imageAlt: 'МойДом — приложение для управляющих компаний',
  },
]
