# Чат-бот Университета «Синергия»

Учебный проект по практике: простой чат-бот, который распознаёт ключевые слова
(интенты) и отвечает на вопросы об организации, поддерживает бытовые темы
(погода, путешествия, еда, small talk), а также оформляет заявку на консультацию.
Исходные данные — в каталоге `sources/`, рабочие базы знаний — в `backend/data/`.

## Возможности

- Распознавание интентов по ключевым словам с лемматизацией русского языка
  (`pymorphy3`), устойчивое к падежам и формам слов.
- Ответы об университете: о вузе, история, лицензия и аккредитация, адрес и
  филиалы, кампус в Дубае, программы и уровни образования, формы и стоимость
  обучения, поступление, руководство и структура, цифровые технологии и ИИ,
  финансы, трудоустройство и контакты.
- Бытовые темы: погода (живые данные Open-Meteo), путешествия и страны, еда и
  рецепты, а также small talk (шутки, «как дела», кто ты и другое).
- Сценарии с уточнением: приём заявки (имя → телефон → направление), погода
  (город), рецепт (блюдо), страна (какая страна). Все — на общем движке FSM.
- Быстрые ответы (кнопки-подсказки) и fallback для непонятных вопросов.
- REST API (FastAPI), SPA на React + TypeScript, Telegram-бот — на общем ядре.

## Архитектура

```
sources/                 исходные данные (Markdown)
  organization-synergy.md
  travel-and-countries.md
  food-and-recipes.md
  everyday-smalltalk.md
  weather-reference.md
backend/
  app/
    knowledge.py     загрузка и слияние баз знаний (knowledge_base + smalltalk)
    nlu.py           нормализация и лемматизация (pymorphy3)
    dialog.py        ядро диалога + универсальный FSM сценариев
    weather.py       Open-Meteo: прогноз и «догадка» при сбое
    recipes.py       справочник рецептов
    countries.py     факты о странах
    engine.py        сборка движка и регистрация resolver'ов
    storage.py       SQLite: сессии и заявки
    schemas.py       Pydantic-схемы
    main.py          FastAPI (/api/chat и др.)
    telegram_bot.py  Telegram-адаптер
  data/
    knowledge_base.json   темы об организации + сценарий заявки
    smalltalk.json        бытовые темы + сценарии погоды, рецепта и страны
  tools/md_to_kb.py  генерация базы знаний из Markdown
  tests/             pytest
frontend/
  src/               React + TypeScript SPA
docker-compose.yml   backend + frontend + bot (профиль)
```

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
npm install
npm run dev
```

## Тесты

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Покрыты распознавание интентов (в том числе бытовых), сценарии заявки, погоды,
рецепта и страны (успех, отмена, повторный запрос), fallback, погодный сервис с
моком сети и эндпоинты API.

## Бытовые темы

Бытовые интенты и сценарии лежат в `backend/data/smalltalk.json` и
автоматически сливаются с `knowledge_base.json` при загрузке:

- **Погода** — `app/weather.py` обращается к бесплатному Open-Meteo (geocoding +
  forecast, без токена). Если сеть недоступна или `WEATHER_ENABLED=false`, бот
  выдаёт случайный вариант и **явно помечает его как догадку**. Если город не
  найден, бот переспрашивает, а не угадывает.
- **Еда** — `recipe` запускает сценарий «какое блюдо?», ответ берётся из
  `app/recipes.py` (борщ, паста, омлет, блины, плов, салат, пицца, суп), иначе
  даётся общий совет.
- **Страны** — `country_info` запускает сценарий «о какой стране?», факты по
  Турции, Египту, ОАЭ, Италии, Франции, Грузии, Японии и Таиланду берутся из
  `app/countries.py`.
- **Путешествия и small talk** — статичные курированные ответы: когда ехать,
  бюджет, безопасность, оформление визы, оплата, ручная кладь; выбор рецепта,
  советы новичкам, выбор заведения и заказ в кафе; извинения, плохое настроение,
  погода и настроение, дождливый день.

Источники для этих тем — `sources/travel-and-countries.md`,
`sources/food-and-recipes.md`, `sources/everyday-smalltalk.md`,
`sources/weather-reference.md`.

## API

| Метод | Путь                 | Описание                          |
|-------|----------------------|-----------------------------------|
| POST  | `/api/chat`          | Сообщение и ответ бота            |
| POST  | `/api/session/reset` | Сброс диалоговой сессии           |
| GET   | `/api/health`        | Проверка работоспособности        |
| GET   | `/api/leads`         | Список заявок (нужен `X-Admin-Token`) |

Пример:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Сколько стоит обучение?"}'
```

```json
{
  "session_id": "…",
  "reply": "Стоимость зависит от программы…",
  "quick_replies": ["Оставить заявку", "Условия поступления", "Формы обучения", "Направления обучения"],
  "state": "idle",
  "intent": "tuition"
}
```

## Как расширять базу знаний

Интенты описаны в `backend/data/knowledge_base.json` (организация) и
`backend/data/smalltalk.json` (бытовые темы). Файлы сливаются загрузчиком:
интенты объединяются (основной файл идёт первым и побеждает при равном весе),
`flows` дополняются новыми из вторичных файлов, `fallback.quick_replies`
объединяются, а `meta` и `settings` берутся только из основного файла. Добавьте
объект в `intents` с полями `id`, `keywords`, `responses`, `quick_replies`.
Порядок ключей не важен — совпадение ищется по леммам, а несколько слов в
ключевой фразе повышают вес совпадения. После правки JSON перезапустите сервис:
база загружается при старте (`uvicorn --reload` реагирует на `.py`, но JSON
подхватит только при рестарте).

Сценарий с уточнением задаётся в `flows`:

```json
"weather": {
  "trigger": "weather_general",
  "cancel_keywords": ["отмена", "стоп"],
  "steps": [{ "key": "city", "prompt": "В каком городе?", "validate": "nonempty", "error": "…" }],
  "resolver": "weather"
}
```

Поле `resolver` ссылается на зарегистрированный обработчик (`engine.py`); если
его нет, используется шаблон `completion`. Для сценария заявки указан
`"store": "lead"`, чтобы результат сохранялся в SQLite.

## Генерация базы знаний из Markdown

Если есть структурированный документ (например, `sources/organization-synergy.md`) с заголовками
`##`/`###`, его можно автоматически превратить в интенты:

```bash
cd backend

# Только интенты из Markdown, служебные части (settings/fallback/flows) — из базового файла
python -m tools.md_to_kb ../sources/organization-synergy.md --base data/knowledge_base.json -o data/knowledge_base.generated.json

# Дополнить существующую базу новыми интентами, не перезаписывая ручные
python -m tools.md_to_kb ../sources/organization-synergy.md --base data/knowledge_base.json --merge -o data/knowledge_base.generated.json

# Без базового файла — со встроенными настройками по умолчанию
python -m tools.md_to_kb ../sources/organization-synergy.md -o data/knowledge_base.generated.json
```

Как это работает:

- каждый заголовок с собственным текстом (по умолчанию от уровня `##`) становится
  интентом: `keywords` — фраза заголовка, значимые слова и синонимы из словаря
  `SYNONYMS`, `responses` — очищенный текст раздела (таблицы разворачиваются в
  строки), `quick_replies` — подзаголовки;
- `--min-level` задаёт минимальный уровень заголовка, `--merge` сохраняет
  существующие интенты, `--base` переносит `settings`, `fallback`, `flows` и
  `meta` из рабочего файла (включая сценарий приёма заявок);
- результат — валидный `knowledge_base.json`, его можно сразу положить вместо
  рабочего и перезапустить сервис.

Точность распознавания всё равно выше у вручную выверенных ключевых слов,
поэтому сгенерированный файл удобно использовать как основу и дорабатывать
`keywords`/`responses` под конкретные формулировки.

## Переменные окружения

| Переменная            | Назначение                                  |
|-----------------------|---------------------------------------------|
| `DB_PATH`             | путь к файлу SQLite                         |
| `KNOWLEDGE_BASE_PATH` | путь к `knowledge_base.json`                |
| `SMALLTALK_PATH`      | путь к `smalltalk.json`                     |
| `WEATHER_ENABLED`     | `true`/`false` — живой прогноз или догадка   |
| `WEATHER_TIMEOUT`     | таймаут запроса к Open-Meteo, секунды        |
| `ADMIN_TOKEN`         | токен для `/api/leads`; пусто — доступ открыт |
| `TELEGRAM_BOT_TOKEN`  | токен Telegram-бота                         |
