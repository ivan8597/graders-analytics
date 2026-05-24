# Проект: загрузка статистики грейдера в PostgreSQL

Итоговый проект курса SkillFactory (модуль «Получение данных из WEB и API»).

## О чём проект

Онлайн-университет (SkillFactory) встроил в свою LMS **грейдер** — редактор кода, который проверяет решения студентов и отправляет оценки обратно в систему обучения.

Каждый день тысячи студентов решают задачи: нажимают **Run** (прогон кода) или **Submit** (сдача на проверку). Эти события сохраняются на стороне провайдера грейдера.

**Наша задача** — выступить как команда аналитики университета:

1. Забирать данные об активности студентов через **REST API**
2. **Обрабатывать и валидировать** ответ
3. **Сохранять** очищенные данные в локальную **PostgreSQL**
4. **Логировать** весь процесс с отловом ошибок
5. *(дополнительно)* визуализировать данные в **Dash-дашборде**

## Что делает скрипт `main.py`

```
API (itresume)  →  обработка и валидация  →  PostgreSQL
                         ↓
                    файл лога (logs/)
```

### 1. Запрос к API

- URL: `https://b2b.itresume.ru/api/statistics`
- Параметры: `client`, `client_key`, `start`, `end` (даты в UTC)
- Библиотека: `requests`

### 2. Обработка данных

Из ответа API извлекаются поля:

| Поле в БД | Откуда берётся |
|-----------|----------------|
| `user_id` | `lti_user_id` |
| `oauth_consumer_key` | из `passback_params` |
| `lis_result_sourcedid` | из `passback_params` |
| `lis_outcome_service_url` | из `passback_params` |
| `is_correct` | из ответа (`null` для run, `0`/`1` для submit) |
| `attempt_type` | `run` или `submit` |
| `created_at` | дата и время попытки |

`passback_params` приходит как строка в формате Python-словаря — разбирается через `ast.literal_eval`.

**Валидация:** некорректные записи пропускаются, причина пишется в лог (`WARNING`).

### 3. Загрузка в PostgreSQL

Таблица `grader_statistics` создаётся автоматически из `sql/create_table.sql`.  
Вставка пакетная через `psycopg2.extras.execute_values`.

### 4. Логирование

- Библиотека `logging`
- Файл: `logs/YYYY-MM-DD.log`
- Уровни: `INFO` (этапы работы), `WARNING` (пропущенные записи), `ERROR` (ошибки API/БД)
- В логах фиксируется **время выполнения** каждого этапа
- Старые логи удаляются — хранятся только за **последние 3 дня**

## Dash-дашборд (`dashboard/`)

Отдельное приложение для визуальной аналитики уже загруженных данных:

- KPI: попытки, студенты, submit, % успешных решений
- Графики активности по дням, run vs submit, успешность submit
- Топ курсов по числу попыток
- Таблица последних попыток

## Структура проекта

```
python/
├── main.py              # ETL: API → обработка → PostgreSQL
├── config.py            # загрузка настроек из .env
├── .env                 # секреты (не коммитить в git)
├── .env.example         # шаблон переменных окружения
├── requirements.txt     # зависимости
├── sql/
│   └── create_table.sql # схема таблицы
├── logs/                # логи работы скрипта
└── dashboard/
    ├── app.py           # Dash-приложение
    └── data.py          # SQL-запросы для графиков
```

## Запуск

### Окружение

```bash
cd /Users/ivanmerkulov/Desktop/python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### База данных и секреты

```bash
createdb grader_db   # если ещё не создана
cp .env.example .env # если файла .env ещё нет
```

Отредактируйте `.env` — ключ API и параметры PostgreSQL:

```env
API_CLIENT_KEY=M2MGWS
DB_USER=postgres
DB_PASSWORD=postgres
```

Файл `.env` в `.gitignore` и не попадает в репозиторий.

### Загрузка данных

```bash
python main.py
```

С параметрами периода:

```bash
python main.py --start "2023-04-01 12:46:47.860798" --end "2023-05-31 23:59:59.999999"
```

### Дашборд

```bash
python -m dashboard.app
```

Открыть в браузере: http://127.0.0.1:8050

## Результат

После успешного запуска `main.py` в базе `grader_db` хранятся сотни тысяч записей о попытках студентов — их можно анализировать SQL-запросами или через Dash.

Пример проверки:

```bash
psql -d grader_db -c "SELECT attempt_type, COUNT(*) FROM grader_statistics GROUP BY attempt_type;"
```
