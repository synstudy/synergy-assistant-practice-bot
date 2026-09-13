# Чат-бот Университета «Синергия»

Учебный проект по практике: чат-бот, который распознаёт ключевые слова (интенты)
и отвечает на вопросы об организации, поддерживает тему погоды и небольшой
small talk, а также оформляет заявку на консультацию. Контентные интенты
генерируются из исходных документов в `sources/`, системный слой (сценарии,
приветствие, help/reset) хранится отдельно в `backend/kb/`.

## Возможности

- Распознавание интентов по ключевым словам с лемматизацией русского языка
  (`pymorphy3`), устойчивое к падежам и формам слов.
- Ответы об университете: название и история, лицензия и аккредитации, адрес,
  филиалы и контакты, международное присутствие и зарубежные кампусы, уровни и
  направления образования, программы и факультеты, формы и форматы обучения,
  стоимость и способы оплаты, поступление, бюджетные места и «Кадровый резерв»,
  трудоустройство и рейтинги, цифровые технологии и ИИ, финансовые показатели,
  конкуренты, судебные дела (данные источников и официального сайта synergy.ru).
- Погода: живые данные Open-Meteo (geocoding + forecast), при сбое сети — явно
  помеченная «догадка», при неизвестном городе — переспрос.
- Small talk: как дела, кто ты, шутки, интересные факты, время/дата, комплименты,
  извинения, плохое настроение.
- Сценарии с уточнением: приём заявки (имя → телефон → направление) и погода
  (город). Общий движок FSM.
- Быстрые ответы (кнопки-подсказки) и fallback для непонятных вопросов.
- Эмуляция набора текста: ответ приходит с задержкой 2–4 секунды
  (`REPLY_DELAY_MIN`/`REPLY_DELAY_MAX`, `0` отключает).
- REST API (FastAPI), SPA на React + TypeScript, Telegram-бот — на общем ядре.

## Архитектура

```
sources/                 исходные данные (Markdown) — источник контента
  organization-synergy.md
  everyday-smalltalk.md
  weather-reference.md   спецификация погоды (интенты не генерируются)
backend/
  app/
    knowledge.py     загрузка и слияние баз знаний
    nlu.py           нормализация и лемматизация (pymorphy3)
    dialog.py        ядро диалога + универсальный FSM сценариев
    weather.py       Open-Meteo: прогноз и «догадка» при сбое
    engine.py        сборка движка и регистрация resolver'ов
    storage.py       SQLite: сессии и заявки
    schemas.py       Pydantic-схемы
    main.py          FastAPI (/api/chat и др.)
    telegram_bot.py  Telegram-адаптер
  kb/
    config.json               source → target + overlay
    knowledge_base.overlay.json
    smalltalk.overlay.json
  data/
    knowledge_base.json   сгенерированные интенты об организации
    smalltalk.json        сгенерированные бытовые интенты
  tools/
    build_kb.py        сборка data/*.json из sources/ + overlay
    md_to_kb.py        низкоуровневый конвертер Markdown → интенты
  tests/               pytest
frontend/
  src/               React + TypeScript SPA
docker-compose.yml   backend + frontend + bot (профиль)
```

## Требования

- Docker и Docker Compose — для запуска стека.
- Python 3.12 — для локального бэкенда и тестов.
- Node.js 20 — для локальной разработки фронтенда.

## Быстрый старт (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- SPA: http://localhost:8080
- API и Swagger: http://localhost:8000/docs

Telegram-бот (при наличии токена в `.env`):

```bash
docker compose --profile bot up --build
```

## Локальная разработка

Бэкенд:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Фронтенд (проксирует `/api` на `localhost:8000`):

```bash
cd frontend
npm ci
npm run dev
```

## Тесты

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Покрыты распознавание системных и контентных интентов, сценарии заявки и погоды
(успех, отмена, повторный запрос), fallback, погодный сервис с моком сети, сборка
базы знаний (`build_kb`) и эндпоинты API.

## Сборка базы знаний из sources

Контентные интенты не пишутся руками, а генерируются из Markdown:

```bash
cd backend
python -m tools.build_kb          # пересобрать data/knowledge_base.json и data/smalltalk.json
python -m tools.build_kb --check  # проверить, что файлы соответствуют sources (exit 1 при расхождении)
```

Как это устроено:

- `kb/config.json` задаёт соответствие: `sources/organization-synergy.md →
  data/knowledge_base.json`, `sources/everyday-smalltalk.md → data/smalltalk.json`.
- каждый заголовок с собственным текстом (`##`/`###`) становится интентом;
  `keywords` — фраза заголовка и значимые слова, `responses` — очищенный текст
  раздела;
- общие однословные ключи (например, «обучения») отбрасываются, чтобы не давать
  ложных срабатываний;
- `kb/*.overlay.json` добавляет системный слой: `meta`, `settings`, `fallback`,
  `flows` (заявка, погода) и системные интенты (`greeting`, `help`, `reset`,
  `lead_request`, `weather_general`, `weather_clothing`, `weather_season`);
- `keyword_overrides` добавляет курируемые алиасы к сгенерированным интентам
  (например, «филиалы» → `regionalnaya-set`, «lms/crm» →
  `sobstvennye-tsifrovye-platformy`).

Файлы `backend/data/*.json` коммитятся (бот работает сразу после клонирования).
После правки `sources/` или overlay пересоберите их и перезапустите сервис: база
загружается при старте.

`tools/md_to_kb.py` — низкоуровневый конвертер произвольного Markdown в интенты
(используется `build_kb`; может применяться отдельно через `python -m
tools.md_to_kb <файл>`).

### Как добавить новую тему

1. Добавьте раздел с заголовками `##`/`###` в существующий `sources/*.md` или
   создайте новый файл.
2. Для нового файла добавьте запись в `kb/config.json` (`source`, `target`,
   `overlay`, `min_level`) и при необходимости — overlay с `flows`/системными
   интентами.
3. Если нужны привычные формулировки, добавьте их в `keyword_overrides` overlay.
4. Выполните `python -m tools.build_kb`, затем перезапустите сервис.

## Бытовые темы

- **Погода** — `app/weather.py` обращается к бесплатному Open-Meteo (без токена).
  Если сеть недоступна или `WEATHER_ENABLED=false`, бот выдаёт случайный вариант и
  **явно помечает его как догадку**. Если город не найден, бот переспрашивает, а не
  угадывает.
- **Small talk** — из `sources/everyday-smalltalk.md` (как дела, кто ты, шутки,
  факты, время, извинения, настроение).
- Спецификация погоды — `sources/weather-reference.md` (коды WMO, варианты
  «догадки», советы по одежде); из неё интенты не генерируются.

## API

| Метод | Путь                 | Описание                          |
|-------|----------------------|-----------------------------------|
| POST  | `/api/chat`          | Сообщение и ответ бота            |
| POST  | `/api/session/reset` | Сброс диалоговой сессии           |
| GET   | `/api/welcome`       | Приветствие и быстрые ответы      |
| GET   | `/api/health`        | Проверка работоспособности        |
| GET   | `/api/leads`         | Список заявок (нужен `X-Admin-Token`) |

Пример:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Филиалы"}'
```

```json
{
  "session_id": "…",
  "reply": "У Университета «Синергия» 94 филиала…",
  "quick_replies": ["Направления подготовки", "Формы обучения", "Филиалы", "Оставить заявку"],
  "state": "idle",
  "intent": "regionalnaya-set"
}
```

## Переменные окружения

| Переменная            | Назначение                                  |
|-----------------------|---------------------------------------------|
| `DB_PATH`             | путь к файлу SQLite                         |
| `KNOWLEDGE_BASE_PATH` | путь к `knowledge_base.json`                |
| `SMALLTALK_PATH`      | путь к `smalltalk.json`                     |
| `CORS_ORIGINS`        | список origin через запятую или `*`          |
| `WEATHER_ENABLED`     | `true`/`false` — живой прогноз или догадка   |
| `WEATHER_TIMEOUT`     | таймаут запроса к Open-Meteo, секунды        |
| `REPLY_DELAY_MIN`     | минимальная задержка ответа, сек (по умолч. 2) |
| `REPLY_DELAY_MAX`     | максимальная задержка ответа, сек; `0` — выключить |
| `ADMIN_TOKEN`         | токен для `/api/leads`; пусто — доступ открыт |
| `TELEGRAM_BOT_TOKEN`  | токен Telegram-бота                         |
