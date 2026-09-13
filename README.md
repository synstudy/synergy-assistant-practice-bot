# Чат-бот Университета «Синергия»

Учебный проект по практике: простой чат-бот, который распознаёт ключевые слова
(интенты) и отвечает на вопросы об организации, а также оформляет заявку на
консультацию. База знаний построена по данным из `data.md` (Университет
«Синергия»).

## Возможности

- Распознавание интентов по ключевым словам с лемматизацией русского языка
  (`pymorphy3`), устойчивое к падежам и формам слов.
- Ответы по разделам: о вузе, история, лицензия и аккредитация, адрес и филиалы,
  кампус в Дубае, программы и уровни образования, формы и стоимость обучения,
  поступление, руководство и структура, цифровые технологии и ИИ, финансы,
  трудоустройство и контакты.
- Многошаговый сценарий **приёма заявок** (имя → телефон → направление) с
  валидацией и сохранением в SQLite.
- Быстрые ответы (кнопки-подсказки) и fallback для непонятных вопросов.
- REST API (FastAPI), SPA на React + TypeScript, Telegram-бот — на общем ядре.

## Архитектура

```
backend/
  app/
    knowledge.py     загрузка базы знаний
    nlu.py           нормализация и лемматизация (pymorphy3)
    dialog.py        ядро диалога + FSM приёма заявок
    storage.py       SQLite: сессии и заявки
    schemas.py       Pydantic-схемы
    main.py          FastAPI (/api/chat и др.)
    telegram_bot.py  Telegram-адаптер
  data/knowledge_base.json
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
pip install -r requirements.txt
pytest -q
```

Покрыты распознавание интентов, сценарий заявки (успех и отмена), fallback и
эндпоинты API.

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
  "quick_replies": ["Оставить заявку", "Условия поступления"],
  "state": "idle",
  "intent": "tuition"
}
```

## Как расширять базу знаний

Интенты описаны в `backend/data/knowledge_base.json` и не требуют правки кода:
добавьте объект в `intents` с полями `id`, `keywords`, `responses`,
`quick_replies`. Порядок ключей не важен — совпадение ищется по леммам, а
несколько слов в ключевой фразе повышают вес совпадения.

## Генерация базы знаний из Markdown

Если есть структурированный документ (например, `data.md`) с заголовками
`##`/`###`, его можно автоматически превратить в интенты:

```bash
cd backend

# Только интенты из Markdown, служебные части (settings/fallback/flows) — из базового файла
python -m tools.md_to_kb ../data.md --base data/knowledge_base.json -o data/knowledge_base.generated.json

# Дополнить существующую базу новыми интентами, не перезаписывая ручные
python -m tools.md_to_kb ../data.md --base data/knowledge_base.json --merge -o data/knowledge_base.generated.json

# Без базового файла — со встроенными настройками по умолчанию
python -m tools.md_to_kb ../data.md -o data/knowledge_base.generated.json
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
| `ADMIN_TOKEN`         | токен для доступа к `/api/leads`            |
| `TELEGRAM_BOT_TOKEN`  | токен Telegram-бота                         |
