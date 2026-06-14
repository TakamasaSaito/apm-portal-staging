import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "apm.db")

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS department (
    department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name     TEXT NOT NULL,
    department_id INTEGER REFERENCES department(department_id),
    role          TEXT NOT NULL DEFAULT 'applicant',
    login_id      TEXT,
    password_hash TEXT
);

CREATE TABLE IF NOT EXISTS application (
    application_id      TEXT PRIMARY KEY,
    application_name    TEXT NOT NULL,
    owner_department_id INTEGER REFERENCES department(department_id),
    status              TEXT NOT NULL DEFAULT 'plan',
    vendor              TEXT,
    business_owner      TEXT,
    system_owner        TEXT,
    ops_manager         TEXT,
    dev_manager         TEXT,
    start_plan          TEXT,
    start_actual        TEXT,
    end_plan            TEXT,
    end_actual          TEXT,
    app_category        TEXT
);

CREATE TABLE IF NOT EXISTS environment (
    environment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id TEXT REFERENCES application(application_id),
    env_type       TEXT NOT NULL,
    location       TEXT,
    ip             TEXT,
    host           TEXT,
    os             TEXT,
    middleware     TEXT,
    cpu_mem        TEXT,
    storage        TEXT
);

CREATE TABLE IF NOT EXISTS configuration_item (
    ci_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ci_name        TEXT NOT NULL,
    ci_type        TEXT,
    environment_id INTEGER REFERENCES environment(environment_id),
    hostname       TEXT,
    ip_address     TEXT,
    bmc_ip         TEXT,
    os             TEXT,
    os_version     TEXT,
    cpu            TEXT,
    memory         TEXT,
    storage        TEXT,
    vendor         TEXT,
    model          TEXT,
    status         TEXT DEFAULT 'active',
    note           TEXT
);

CREATE TABLE IF NOT EXISTS apm_request (
    request_id        TEXT PRIMARY KEY,
    type              TEXT NOT NULL,
    application_id    TEXT REFERENCES application(application_id),
    applicant_user_id INTEGER REFERENCES user(user_id),
    applied_at        TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'pending',
    approver_user_id  INTEGER REFERENCES user(user_id),
    approved_at       TEXT,
    reason            TEXT,
    changes           TEXT,
    app_name          TEXT,
    dept              TEXT,
    biz_owner         TEXT,
    new_status        TEXT,
    start_plan        TEXT,
    end_plan          TEXT,
    app_category      TEXT
);
        """)
        # Migration: add login columns to existing databases
        for stmt in (
            "ALTER TABLE user ADD COLUMN login_id TEXT",
            "ALTER TABLE user ADD COLUMN password_hash TEXT",
            "ALTER TABLE application ADD COLUMN app_category TEXT",
            "ALTER TABLE apm_request ADD COLUMN app_category TEXT",
        ):
            try:
                await db.execute(stmt)
            except Exception:
                pass
        await db.commit()
