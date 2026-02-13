# Block 4: Database Layer — Context & Implementation Log

## Status: COMPLETED

## Project State Before Block 4
- Blocks 1-3 completed: bot startup, LLM providers (Groq/Anthropic/OpenAI), text analysis handler
- All database files existed as empty stubs
- No alembic.ini existed, migrations/env.py and script.py.mako were empty
- DATABASE_URL configured in .env: `sqlite+aiosqlite:///./mindlint.db`

## Key Architecture Decisions
- **ORM**: SQLAlchemy 2.x async with DeclarativeBase
- **Driver**: aiosqlite (async SQLite)
- **Migrations**: Alembic with async engine support (asyncio.run in env.py)
- **Pattern**: Repository pattern for data access (static methods)
- **Session injection**: aiogram middleware via `data["session"]` on `dp.update`

## Files Modified/Created in Block 4

| File | Action | Description |
|------|--------|-------------|
| `app/database/models/base.py` | Implemented | Base(DeclarativeBase) with id (Integer PK), created_at (DateTime) |
| `app/database/models/user.py` | Implemented | User model: telegram_id, username, first_name, language_code, analysis_count, last_active_at, is_active, settings_json |
| `app/database/models/analysis.py` | Implemented | Analysis model: user_id (FK→users.id), user_message, bot_response, llm_provider, llm_model, tokens_used |
| `app/database/models/__init__.py` | Updated | Re-exports Base, User, Analysis |
| `app/database/engine.py` | Implemented | create_async_engine, async_sessionmaker, create_tables() |
| `app/database/__init__.py` | Updated | Re-exports engine, async_session, create_tables |
| `app/database/repositories/user.py` | Implemented | UserRepository: get_or_create, update_last_active, increment_analysis_count, get_stats |
| `app/database/repositories/analysis.py` | Implemented | AnalysisRepository: create, get_by_user (with pagination), count_by_user |
| `app/database/repositories/__init__.py` | Updated | Re-exports UserRepository, AnalysisRepository |
| `app/middlewares/database.py` | Implemented | DatabaseMiddleware — creates AsyncSession per request, rollback on error |
| `app/handlers/analyze.py` | Updated | Added: get_or_create user, save analysis to DB, increment count, update last_active |
| `app/bot.py` | Updated | Added register_middlewares() with DatabaseMiddleware on dp.update |
| `main.py` | Updated | Added await create_tables() before start_polling |
| `alembic.ini` | Created | Alembic config: script_location=migrations, sqlite+aiosqlite URL |
| `migrations/env.py` | Implemented | Async env: run_async_migrations() with create_async_engine, uses app.config.settings |
| `migrations/script.py.mako` | Created | Standard Mako template for migrations |
| `migrations/versions/88b8caaca69e_...py` | Auto-generated | First migration: CREATE users + analyses tables with indexes |

## Database Schema

### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, autoincrement |
| telegram_id | BigInteger | unique, not null, indexed |
| username | String(255) | nullable |
| first_name | String(255) | nullable |
| language_code | String(10) | nullable |
| analysis_count | Integer | default 0, server_default "0" |
| created_at | DateTime | default utcnow, server_default CURRENT_TIMESTAMP |
| last_active_at | DateTime | nullable |
| is_active | Boolean | default True, server_default "1" |
| settings_json | Text | nullable |

### analyses
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, autoincrement |
| user_id | Integer | FK -> users.id, not null, indexed |
| user_message | Text | not null |
| bot_response | Text | not null |
| llm_provider | String(50) | nullable |
| llm_model | String(100) | nullable |
| tokens_used | Integer | default 0, server_default "0" |
| created_at | DateTime | default utcnow, server_default CURRENT_TIMESTAMP |

### Relationships
- `User.analyses` -> `list[Analysis]` (one-to-many, back_populates, lazy="selectin")
- `Analysis.user` -> `User` (many-to-one, back_populates)

## Repository API

### UserRepository (static methods)
- `get_or_create(session, telegram_id, **kwargs) -> User` — найти или создать пользователя
- `update_last_active(session, telegram_id)` — обновить last_active_at на utcnow
- `increment_analysis_count(session, telegram_id)` — увеличить analysis_count на 1
- `get_stats(session) -> dict` — {total_users, active_users, total_analyses}

### AnalysisRepository (static methods)
- `create(session, user_id, user_message, bot_response, llm_provider, llm_model, tokens_used) -> Analysis`
- `get_by_user(session, user_id, limit=10, offset=0) -> list[Analysis]` — с пагинацией, DESC по created_at
- `count_by_user(session, user_id) -> int`

## Data Flow (analyze handler)
1. User sends text message
2. DatabaseMiddleware creates AsyncSession, passes as `data["session"]`
3. Handler receives `session` parameter (aiogram DI)
4. `UserRepository.get_or_create()` — find/create user by telegram_id
5. `AnalysisService.analyze()` — call LLM
6. `AnalysisRepository.create()` — save message + response to DB
7. `UserRepository.increment_analysis_count()` + `update_last_active()`
8. Send response parts to user
9. DatabaseMiddleware closes session (rollback on error)

## Dependencies
All required packages already in requirements.txt:
- `sqlalchemy[asyncio]`
- `aiosqlite`
- `alembic`

## Verification
- All imports verified OK
- End-to-end test: create user -> create analysis -> query -> stats — all passed
- Alembic autogenerate detected both tables with correct columns, indexes, and FK
- Middleware + dispatcher integration verified

## Notes for Future Blocks
- Block 6 (Patterns): may need new model/table for pattern tracking
- Block 8 (Admin): use `UserRepository.get_stats()` for admin dashboard
- Block 9 (Settings): use `User.settings_json` field for per-user settings storage
- When modifying models, always create a new Alembic migration: `alembic revision --autogenerate -m "description"`

---

# Block 5: Journal /journal — Context & Implementation Log

## Status: COMPLETED

## Files Modified/Created in Block 5

| File | Action | Description |
|------|--------|-------------|
| `app/services/journal.py` | Implemented | JournalService: get_user_journal, get_total_pages, get_analysis_detail |
| `app/keyboards/inline.py` | Implemented | journal_page_kb (entries + nav), journal_detail_back_kb |
| `app/handlers/journal.py` | Implemented | /journal command, callback handlers for pagination and detail view |
| `app/handlers/start.py` | Updated | Added /journal to /help command list |
| `app/bot.py` | Updated | Registered journal_router (after start, before analyze) |
| `app/database/repositories/analysis.py` | Updated | Added get_by_id() method |

## Architecture

### JournalService API (`app/services/journal.py`)
- `get_user_journal(session, telegram_id, page, per_page=5) -> list[dict]` — paginated entries with truncated text
- `get_total_pages(session, telegram_id, per_page=5) -> int` — total page count
- `get_analysis_detail(session, analysis_id) -> Analysis | None` — full analysis for detail view

### Inline Keyboards (`app/keyboards/inline.py`)
- `journal_page_kb(entries, page, total_pages)` — entry buttons + navigation row
- `journal_detail_back_kb(page)` — back to list button

### Callback Data Format
- `journal:page:{N}` — navigate to page N
- `journal:detail:{analysis_id}` — show full analysis
- `journal:noop` — page indicator (no action)

### Handler Flow
1. `/journal` -> show page 1 (or "no entries" message)
2. Click entry button -> edit message with full analysis + back button
3. Click nav buttons -> edit message with new page
4. Click "back" -> return to page list

## Router Registration Order
`start_router` -> `journal_router` -> `analyze_router` (catch-all last)

## Verification
- All imports OK
- Page 1: 5 entries, Page 2: 2 entries (7 total, per_page=5) -> 2 pages
- get_by_id works for existing/non-existing IDs
- Keyboard generates correct rows (entries + navigation)

---

# Block 6: Patterns /patterns — Context & Implementation Log

## Status: COMPLETED

## Files Modified/Created in Block 6

| File | Action | Description |
|------|--------|-------------|
| `app/services/pattern_tracker.py` | Implemented | PATTERNS dict, detect_patterns(), PatternTracker class |
| `app/handlers/patterns.py` | Implemented | /patterns command handler |
| `app/database/models/analysis.py` | Updated | Added `detected_patterns` (Text, nullable) |
| `app/database/repositories/analysis.py` | Updated | Added `detected_patterns` param to create() |
| `app/handlers/analyze.py` | Updated | Detects patterns in LLM response, saves to DB |
| `app/handlers/start.py` | Updated | Added /patterns to /help |
| `app/bot.py` | Updated | Registered patterns_router |
| `migrations/versions/6e9a3405ea7b_...py` | Auto-generated | ADD COLUMN detected_patterns to analyses |

## 5 Patterns (from system_prompt.txt)

| Code | Name | Detection Markers |
|------|------|-------------------|
| A | Подмена причины ощущением | "паттерн a", "подмена причины", "не могу без метрик" |
| B | Ложная необходимость | "паттерн b", "ложная необходимость", "нужно сначала" |
| C | Циклическая логика | "паттерн c", "циклическая логика", "замкнутый круг" |
| D | Неопределённое условие | "паттерн d", "неопределённое условие", "когда буду готов" |
| E | Универсальное оправдание | "паттерн e", "универсальное оправдание", "одна причина объясняет" |

## Architecture

### detect_patterns(bot_response) -> list[str]
- Regex-based detection of pattern codes in LLM response text
- Returns list of found codes, e.g. `["A", "D"]`

### PatternTracker API
- `get_user_patterns(session, telegram_id) -> dict` — loads all analyses, counts patterns
- `format_patterns_text(data) -> str` — formats with progress bars and HTML

### Storage
- `detected_patterns` field in analyses table stores JSON list: `["A", "D"]`
- Filled on each new analysis in analyze handler
- Fallback: if field is empty, re-parses bot_response on the fly

## Router Registration Order
`start_router` -> `journal_router` -> `patterns_router` -> `analyze_router`

## Verification
- All 5 patterns detected correctly from test responses
- Empty response returns `[]`
- PatternTracker aggregation works: 5 analyses -> correct counts per pattern
- Progress bar visualization: `█████` filled proportionally to max count
- `< 3 analyses` shows "need more data" message

---

# Block 7: FSM Multi-Turn Dialogue — Context & Implementation Log

## Status: COMPLETED

## Files Modified/Created in Block 7

| File | Action | Description |
|------|--------|-------------|
| `app/states/analysis.py` | Implemented | AnalysisStates(StatesGroup) with waiting_for_clarification |
| `app/services/llm/base.py` | Updated | Added abstract generate_with_history() |
| `app/services/llm/groq.py` | Updated | Implemented generate_with_history() |
| `app/services/llm/openai.py` | Updated | Implemented generate_with_history() |
| `app/services/llm/anthropic.py` | Updated | Implemented generate_with_history() |
| `app/services/analysis.py` | Updated | Added continue_analysis(history, new_message) |
| `app/keyboards/inline.py` | Updated | Added analysis_actions_kb() with Clarify/Finish buttons |
| `app/handlers/analyze.py` | Rewritten | FSM logic: initial analysis -> buttons -> clarification loop |

## Architecture

### FSM Flow
```
User sends text
    -> handle_text(): analyze, save, show buttons [Уточнить | Завершить]
    -> state.update_data(history=[...])

User clicks "Уточнить"
    -> cb_clarify(): set state waiting_for_clarification
    -> "Напишите уточнение..."

User sends clarification text
    -> handle_clarification(): continue_analysis with full history
    -> save to DB, update history, show buttons again

User clicks "Завершить"
    -> cb_finish(): state.clear()
```

### LLM Provider Changes
- `generate_with_history(system_prompt, messages)` — sends full conversation as messages list
- Groq/OpenAI: system message + messages list
- Anthropic: system param + messages list (Anthropic API style)

### Callback Data
- `analysis:clarify` — enter clarification mode
- `analysis:finish` — clear FSM, end dialogue

### Handler Order in analyze_router
1. `handle_clarification` — state filter `AnalysisStates.waiting_for_clarification` (FIRST, state-specific)
2. `cb_clarify` / `cb_finish` — callback handlers
3. `handle_text` — catch-all for text without state (LAST)

## Verification
- All imports OK
- FSM state registered: `AnalysisStates:waiting_for_clarification`
- Keyboard: 2 buttons (clarify + finish)
- continue_analysis method exists in AnalysisService
- All 3 providers have generate_with_history()

---

# Block 8: Admin Panel & Security — Context & Implementation Log

## Status: COMPLETED

## Files Modified/Created in Block 8

| File | Action | Description |
|------|--------|-------------|
| `app/filters/admin.py` | Implemented | IsAdmin(Filter) — checks user.id in settings.admin_ids |
| `app/middlewares/admin_check.py` | Implemented | Logs non-admin attempts to use /stats, /broadcast |
| `app/middlewares/throttling.py` | Implemented | Rate limiting: 5 messages per 60s per user |
| `app/handlers/admin.py` | Implemented | /stats (full stats), /broadcast (send to all active users) |
| `app/bot.py` | Updated | Added AdminCheckMiddleware, ThrottlingMiddleware, admin_router |
| `app/database/repositories/user.py` | Updated | Extended get_stats() with today stats, added get_active_users() |

## Architecture

### IsAdmin Filter
- Applied to entire `admin_router` via `admin_router.message.filter(IsAdmin())`
- Non-admin users' messages to /stats, /broadcast simply won't match

### Middleware Order
1. `DatabaseMiddleware` (on `dp.update`) — session for all events
2. `AdminCheckMiddleware` (on `dp.message`) — logs unauthorized attempts
3. `ThrottlingMiddleware` (on `dp.message`) — rate limits messages

### ThrottlingMiddleware
- In-memory dict `{user_id: [timestamp, ...]}` with sliding window
- Max 5 messages per 60 seconds
- Expired timestamps cleaned on each check
- Shows "Подождите немного..." on throttle

### Router Registration Order
`start` -> `admin` -> `journal` -> `patterns` -> `analyze` (catch-all last)

### /stats Output
- Total users, active users, active today
- Total analyses, analyses today

### /broadcast
- `/broadcast <text>` — sends to all active users
- Reports sent/failed counts

## Verification
- All imports OK
- Router order: ['start', 'admin', 'journal', 'patterns', 'analyze']
- get_stats returns 5 fields including today metrics
- get_active_users returns all is_active=True users
