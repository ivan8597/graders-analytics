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
5. **Визуализировать данные в Dash-дашборде**

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

**Схема таблицы:**

| Колонка | Тип | Описание |
|---------|-----|----------|
| `id` | `SERIAL` | Первичный ключ |
| `user_id` | `VARCHAR(64)` | ID студента (`lti_user_id`) |
| `oauth_consumer_key` | `VARCHAR(255)` | Ключ LTI-потребителя |
| `lis_result_sourcedid` | `TEXT` | Идентификатор результата в LMS |
| `lis_outcome_service_url` | `TEXT` | URL сервиса оценок |
| `is_correct` | `BOOLEAN` | `NULL` для run, `TRUE`/`FALSE` для submit |
| `attempt_type` | `VARCHAR(16)` | `run` или `submit` |
| `created_at` | `TIMESTAMP` | Время попытки (UTC) |

Индексы: `user_id`, `created_at`.

Пример DDL (полный файл — `sql/create_table.sql`):

```sql
CREATE TABLE IF NOT EXISTS grader_statistics (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    oauth_consumer_key VARCHAR(255),
    lis_result_sourcedid TEXT NOT NULL,
    lis_outcome_service_url TEXT NOT NULL,
    is_correct BOOLEAN,
    attempt_type VARCHAR(16) NOT NULL,
    created_at TIMESTAMP NOT NULL
);
```

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

Клонировали репозиторий с GitHub и запускаете с нуля.

### Что должно быть установлено

| Программа | Зачем |
|-----------|--------|
| **Python 3.10+** | скрипт и дашборд |
| **PostgreSQL 14+** | локальная база |
| **Git** | скачать проект |

Проверка в терминале:

```bash
python3 --version
psql --version
git --version
```

На macOS PostgreSQL часто ставят через Homebrew: `brew install postgresql@14`, затем `brew services start postgresql@14`.

### 1. Скачать проект

```bash
git clone https://github.com/ВАШ_ЛОГИН/ВАШ_РЕПОЗИТОРИЙ.git
cd ВАШ_РЕПОЗИТОРИЙ
```

Подставьте свой URL репозитория с GitHub.

### 2. Виртуальное окружение и зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. База данных PostgreSQL

Убедитесь, что сервер запущен (`pg_isready`).

Создайте базу (один раз):

```bash
createdb grader_db
```

Если `createdb` пишет «already exists» — это нормально, база уже есть.

### 4. Файл настроек `.env`

В репозитории есть только шаблон `.env.example` — секреты в git не попадают.

```bash
cp .env.example .env
```

Откройте `.env` и укажите свои значения:

```env
API_CLIENT_KEY=M2MGWS

DB_HOST=localhost
DB_PORT=5432
DB_NAME=grader_db
DB_USER=postgres
DB_PASSWORD=postgres
```

На Mac часто пользователь БД совпадает с именем учётной записи системы (без пароля), например:

```env
DB_USER=ivanmerkulov
DB_PASSWORD=
```

Проверка подключения:

```bash
psql -h localhost -d grader_db -c "SELECT 1;"
```

### 5. Загрузка данных из API в PostgreSQL

```bash
source .venv/bin/activate
python main.py
```

Полный период по умолчанию (апрель–май 2023) качается **долго** (несколько минут). Для быстрой проверки:

```bash
python main.py --start "2023-05-31 00:00:00.000000" --end "2023-05-31 01:00:00.000000"
```

Лог пишется в `logs/YYYY-MM-DD.log`.

### 6. Dash-дашборд

Нужны уже загруженные данные в `grader_db`.

```bash
source .venv/bin/activate
python -m dashboard.app
```

В браузере: **http://127.0.0.1:8050**


Если порт занят:

```bash
kill $(lsof -t -i:8050)
# или другой порт:
DASH_PORT=8051 python -m dashboard.app
```

### 7. Проверка данных в БД

```bash
psql -d grader_db -c "SELECT COUNT(*) FROM grader_statistics;"
psql -d grader_db -c "SELECT attempt_type, COUNT(*) FROM grader_statistics GROUP BY attempt_type;"
```

### Частые проблемы

| Симптом | Решение |
|---------|---------|
| `API_CLIENT_KEY не задан` | Создайте `.env` из `.env.example` |
| `connection refused` (PostgreSQL) | Запустите сервер: `brew services start postgresql@14` |
| `role "postgres" does not exist` | Укажите в `.env` своего пользователя (`whoami`) |
| `Port 8050 is in use` | Закройте старый Dash или смените `DASH_PORT` |
| Долго висит на «Скачивание из API» | Подождите или сузьте период `--start` / `--end` |

### Что не переносится через Git

Не клонируются (нужно создать локально):

- `.env` — скопировать из `.env.example`
- `.venv/` — создать заново (`python3 -m venv .venv`)
- `logs/` — появятся после запуска `main.py`
- данные в PostgreSQL — при необходимости снова выполнить `python main.py`

## Запуск (кратко, если проект уже настроен)

```bash
source .venv/bin/activate
python main.py
python -m dashboard.app
```
