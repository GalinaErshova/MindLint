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
- Block 5 (Journal): use `AnalysisRepository.get_by_user()` with pagination for /journal
- Block 6 (Patterns): may need new model/table for pattern tracking
- Block 8 (Admin): use `UserRepository.get_stats()` for admin dashboard
- Block 9 (Settings): use `User.settings_json` field for per-user settings storage
- When modifying models, always create a new Alembic migration: `alembic revision --autogenerate -m "description"`
