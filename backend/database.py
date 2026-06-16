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

CREATE TABLE IF NOT EXISTS demand (
  demand_id      TEXT PRIMARY KEY,
  title          TEXT NOT NULL,
  it_class       TEXT,
  category       TEXT,
  domain         TEXT,
  type           TEXT,
  start_date     DATE,
  due_date       DATE,
  submitter_user_id   INTEGER REFERENCES user(user_id),
  department_id       INTEGER REFERENCES department(department_id),
  manager_user_id     INTEGER REFERENCES user(user_id),
  system_owner_user_id INTEGER REFERENCES user(user_id),
  pm_user_id          INTEGER REFERENCES user(user_id),
  description    TEXT,
  portfolio      TEXT,
  program        TEXT,
  change_type    TEXT,
  purpose        TEXT,
  feasibility    TEXT,
  priority       TEXT,
  region         TEXT,
  company        TEXT,
  business_unit  TEXT,
  business_case  TEXT,
  expected_benefit TEXT,
  target_date    DATE,
  estimated_cost INTEGER,
  requested_budget INTEGER,
  cost_note      TEXT,
  notes          TEXT,
  stage          TEXT DEFAULT 'draft',
  reject_reason  TEXT,
  review_comment TEXT,
  approval_comment TEXT,
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demand_application (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  demand_id      TEXT REFERENCES demand(demand_id),
  application_id TEXT REFERENCES application(application_id),
  relation_note  TEXT
);

CREATE TABLE IF NOT EXISTS cost_plan (
  cost_plan_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  demand_id      TEXT REFERENCES demand(demand_id),
  fiscal_year    INTEGER,
  fiscal_period  TEXT,
  cost_type      TEXT,
  unit_cost      INTEGER,
  quantity       INTEGER DEFAULT 1,
  planned_cost   INTEGER,
  actual_cost    INTEGER DEFAULT 0,
  note           TEXT,
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demand_task (
  task_id        TEXT PRIMARY KEY,
  demand_id      TEXT REFERENCES demand(demand_id),
  name           TEXT NOT NULL,
  due_date       DATE,
  assignee_user_id INTEGER REFERENCES user(user_id),
  priority       TEXT,
  state          TEXT DEFAULT 'open',
  comment        TEXT,
  ai_generated   INTEGER DEFAULT 0,
  rationale      TEXT,
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project (
  project_id     TEXT PRIMARY KEY,
  demand_id      TEXT REFERENCES demand(demand_id),
  title          TEXT NOT NULL,
  status         TEXT DEFAULT 'active',
  created_date   DATE,
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

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
    application_id       TEXT PRIMARY KEY,
    application_name     TEXT NOT NULL,
    owner_department_id  INTEGER REFERENCES department(department_id),
    status               TEXT NOT NULL DEFAULT 'plan',
    vendor               TEXT,
    business_owner       TEXT,
    system_owner         TEXT,
    ops_manager          TEXT,
    dev_manager          TEXT,
    start_plan           TEXT,
    start_actual         TEXT,
    end_plan             TEXT,
    end_actual           TEXT,
    app_category         TEXT,
    portfolio_area       INTEGER,
    migration_target_id  TEXT REFERENCES application(application_id),
    annual_cost_million  INTEGER,
    is_infrastructure    INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS application_dependency (
    dependency_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id            TEXT REFERENCES application(application_id),
    depends_on_app_id TEXT REFERENCES application(application_id),
    dependency_type   TEXT,
    note              TEXT
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
        for stmt in (
            "ALTER TABLE user ADD COLUMN login_id TEXT",
            "ALTER TABLE user ADD COLUMN password_hash TEXT",
            "ALTER TABLE application ADD COLUMN app_category TEXT",
            "ALTER TABLE application ADD COLUMN portfolio_area INTEGER",
            "ALTER TABLE application ADD COLUMN migration_target_id TEXT",
            "ALTER TABLE application ADD COLUMN annual_cost_million INTEGER",
            "ALTER TABLE application ADD COLUMN is_infrastructure INTEGER DEFAULT 0",
            "ALTER TABLE application ADD COLUMN vendor TEXT",
            "ALTER TABLE apm_request ADD COLUMN app_category TEXT",
        ):
            try:
                await db.execute(stmt)
            except Exception:
                pass
        await db.commit()
