"""初期データ投入スクリプト。既存データをクリアして再投入する。"""
import sqlite3
import json
import os
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash(pw: str) -> str:
    return _pwd_context.hash(pw)


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "apm.db")


def seed():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.executescript("""
PRAGMA foreign_keys = OFF;

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
    migration_target_id  TEXT,
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

    # Migration: add columns to existing databases
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
            cur.execute(stmt)
        except Exception:
            pass

    # demand/project テーブル作成（存在しない場合）
    cur.executescript("""
CREATE TABLE IF NOT EXISTS demand (
  demand_id      TEXT PRIMARY KEY,
  title          TEXT NOT NULL,
  it_class       TEXT,
  category       TEXT,
  domain         TEXT,
  type           TEXT,
  start_date     DATE,
  due_date       DATE,
  submitter_user_id   INTEGER,
  department_id       INTEGER,
  manager_user_id     INTEGER,
  system_owner_user_id INTEGER,
  pm_user_id          INTEGER,
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
  demand_id      TEXT,
  application_id TEXT,
  relation_note  TEXT
);

CREATE TABLE IF NOT EXISTS cost_plan (
  cost_plan_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  demand_id      TEXT,
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
  demand_id      TEXT,
  name           TEXT NOT NULL,
  due_date       DATE,
  assignee_user_id INTEGER,
  priority       TEXT,
  state          TEXT DEFAULT 'open',
  comment        TEXT,
  ai_generated   INTEGER DEFAULT 0,
  rationale      TEXT,
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project (
  project_id     TEXT PRIMARY KEY,
  demand_id      TEXT,
  title          TEXT NOT NULL,
  status         TEXT DEFAULT 'active',
  created_date   DATE,
  created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS relation_type (
  relation_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
  type_name        TEXT NOT NULL UNIQUE,
  parent_label     TEXT,
  child_label      TEXT
);

CREATE TABLE IF NOT EXISTS cmdb_rel_ci (
  rel_id           INTEGER PRIMARY KEY AUTOINCREMENT,
  parent_table     TEXT NOT NULL,
  parent_id        TEXT NOT NULL,
  child_table      TEXT NOT NULL,
  child_id         TEXT NOT NULL,
  relation_type_id INTEGER,
  note             TEXT,
  created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);
    """)

    # スキーマ強制移行: environment / configuration_item から直接FKカラムを除去
    cur.executescript("""
DROP TABLE IF EXISTS environment;
CREATE TABLE environment (
    environment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    env_type       TEXT NOT NULL,
    location       TEXT, ip TEXT, host TEXT, os TEXT,
    middleware     TEXT, cpu_mem TEXT, storage TEXT
);
DROP TABLE IF EXISTS configuration_item;
CREATE TABLE configuration_item (
    ci_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ci_name        TEXT NOT NULL, ci_type TEXT,
    hostname       TEXT, ip_address TEXT, bmc_ip TEXT,
    os TEXT, os_version TEXT, cpu TEXT, memory TEXT, storage TEXT,
    vendor TEXT, model TEXT,
    status         TEXT DEFAULT 'active', note TEXT
);
    """)

    # relation_type 初期データ投入
    cur.execute("INSERT OR IGNORE INTO relation_type (type_name, parent_label, child_label) VALUES ('has_environment','環境を持つ','環境である')")
    cur.execute("INSERT OR IGNORE INTO relation_type (type_name, parent_label, child_label) VALUES ('has_ci','構成情報を持つ','構成情報である')")

    # 既存データクリア（FK OFF なので順序自由）
    for table in [
        "cmdb_rel_ci",
        "cost_plan", "demand_application", "demand_task", "project", "demand",
        "apm_request", "configuration_item", "environment",
        "application_dependency", "application", "user", "department",
    ]:
        cur.execute(f"DELETE FROM {table}")

    # ---------- 部署（20件） ----------
    departments = [
        "人事部", "営業本部", "購買部", "経理部", "総務部",
        "情報システム部", "開発部", "品質管理部", "法務部", "マーケティング部",
        "海外事業部", "製造部", "物流部", "カスタマーサポート部", "広報部",
        "財務部", "経営企画部", "内部監査部", "調達部", "研修部",
    ]
    dept_ids: dict = {}
    for d in departments:
        cur.execute("INSERT INTO department (department_name) VALUES (?)", [d])
        dept_ids[d] = cur.lastrowid

    # ---------- ユーザー（20件） ----------
    users = [
        # name,           dept,                   role,        login_id, password_hash
        ("申請者ユーザー", "情報システム部",   "applicant", "user",  _hash("user")),   # 既存 user/user
        ("事務局ユーザー", "情報システム部",   "admin",     "admin", _hash("admin")),  # 既存 admin/admin
        # ── 以下 18 名追加（既存名称は維持し dept を更新）──
        ("田中 花子",      "人事部",           "applicant", None, None),
        ("山田 太郎",      "情報システム部",   "applicant", None, None),
        ("鈴木 一郎",      "経理部",           "applicant", None, None),
        ("高橋 二郎",      "営業本部",         "applicant", None, None),
        ("佐藤 事務局",    "情報システム部",   "admin",     None, None),
        ("伊藤 三郎",      "購買部",           "applicant", None, None),
        ("渡辺 四郎",      "総務部",           "applicant", None, None),
        ("中村 五郎",      "開発部",           "applicant", None, None),
        ("小林 六子",      "品質管理部",       "applicant", None, None),
        ("加藤 七子",      "法務部",           "admin",     None, None),
        ("吉田 八郎",      "マーケティング部", "applicant", None, None),
        ("山本 九子",      "海外事業部",       "applicant", None, None),
        ("松本 十郎",      "製造部",           "applicant", None, None),
        ("井上 勇",        "物流部",           "applicant", None, None),
        ("木村 梅子",      "カスタマーサポート部", "applicant", None, None),
        ("林 竹子",        "広報部",           "applicant", None, None),
        ("清水 松子",      "財務部",           "admin",     None, None),
        ("藤田 健",        "経営企画部",       "applicant", None, None),
    ]
    user_ids: dict = {}
    for name, dept, role, login_id, password_hash in users:
        cur.execute(
            "INSERT INTO user (user_name, department_id, role, login_id, password_hash) VALUES (?, ?, ?, ?, ?)",
            [name, dept_ids[dept], role, login_id, password_hash],
        )
        user_ids[name] = cur.lastrowid

    # ---------- アプリケーション（20件） ----------
    # (id, name, dept, status, vendor,
    #  biz_owner, sys_owner, ops_mgr, dev_mgr,
    #  start_plan, start_actual, end_plan, end_actual, app_category,
    #  portfolio_area, migration_target_id, annual_cost_million, is_infrastructure)
    apps = [
        # ── グローバル基盤（migration_target として参照される）──
        ("G-CLOUD", "グローバルクラウド基盤(AWS)",    "情報システム部", "running",
         "Amazon Web Services",
         "事務局ユーザー", "山田 太郎", "山田 太郎", "山田 太郎",
         "2022-04-01", "2022-04-01", None, None,
         "Cloud Platform（クラウド基盤）",
         4, None, 6200, 1),

        ("G-SSO",   "グローバル認証基盤(SSO)",        "情報システム部", "running",
         "Microsoft Azure AD",
         "事務局ユーザー", "山田 太郎", "山田 太郎", "山田 太郎",
         "2023-01-01", "2023-01-01", None, None,
         "Security（セキュリティ管理）",
         4, None, 3800, 1),

        ("G-HRM",   "グローバルHRM",                  "人事部",         "dev",
         "Workday",
         "田中 花子", "田中 花子", "田中 花子", "中村 五郎",
         "2026-10-01", None, None, None,
         "HRM（人事・労務・給与）",
         4, None, 4800, 0),

        ("G-ERP",   "グローバルERP",                  "経理部",         "running",
         "SAP",
         "鈴木 一郎", "鈴木 一郎", "鈴木 一郎", "中村 五郎",
         "2023-07-01", "2023-07-01", None, None,
         "ERP（基幹業務）",
         4, None, 5500, 0),

        # ── 国内インフラ ──
        ("INF-DC1",  "国内データセンター基盤",         "情報システム部", "running",
         "NTTデータ",
         "事務局ユーザー", "山田 太郎", "山田 太郎", "山田 太郎",
         "2015-04-01", "2015-04-01", "2027-03-31", None,
         "Infrastructure（インフラ・サーバー・クラウド）",
         2, "G-CLOUD", 1200, 1),

        ("INF-AUTH", "国内認証基盤",                   "情報システム部", "running",
         "株式会社ID管理",
         "事務局ユーザー", "山田 太郎", "山田 太郎", "山田 太郎",
         "2016-06-01", "2016-06-01", "2026-09-30", None,
         "Security（セキュリティ管理）",
         2, "G-SSO", 900, 1),

        # ── 業務アプリ APM-001〜APM-007（既存） ──
        ("APM-001", "人事管理システム",                "人事部",         "running",
         "株式会社HR-Tech",
         "田中 花子", "田中 花子", "山田 太郎", "中村 五郎",
         "2021-04-01", "2021-04-01", "2028-03-31", None,
         "HRM（人事・労務・給与）",
         2, None, 850, 0),

        ("APM-002", "営業支援システム（SFA）",         "営業本部",       "running",
         "Salesforce Japan",
         "高橋 二郎", "高橋 二郎", "山田 太郎", "中村 五郎",
         "2020-10-01", "2020-10-15", "2027-09-30", None,
         "CRM（顧客管理・営業支援）",
         2, None, 620, 0),

        ("APM-003", "在庫管理システム",                "購買部",         "running",
         "株式会社SCM-Pro",
         "伊藤 三郎", "伊藤 三郎", "山田 太郎", "中村 五郎",
         "2019-07-01", "2019-07-01", "2027-06-30", None,
         "SCM（サプライチェーン・購買・在庫）",
         2, None, 480, 0),

        ("APM-004", "経費精算システム",                "経理部",         "running",
         "株式会社FinTech",
         "鈴木 一郎", "鈴木 一郎", "山田 太郎", "中村 五郎",
         "2022-01-01", "2022-02-01", "2029-03-31", None,
         "Finance（経理・財務・予算）",
         2, None, 520, 0),

        ("APM-005", "顧客管理システム（CRM）",         "営業本部",       "dev",
         "Salesforce Japan",
         "高橋 二郎", "高橋 二郎", "山田 太郎", "中村 五郎",
         "2025-10-01", None, None, None,
         "CRM（顧客管理・営業支援）",
         3, None, 720, 0),

        ("APM-006", "文書管理システム",                "総務部",         "plan",
         "未定",
         "渡辺 四郎", "渡辺 四郎", "未定", "未定",
         "2026-10-01", None, None, None,
         "Document Management（文書・コンテンツ管理）",
         3, None, 380, 0),

        ("APM-007", "旧給与計算システム",              "人事部",         "retire",
         "株式会社レガシーSI",
         "田中 花子", "田中 花子", "退任", "退任",
         "2010-04-01", "2010-04-01", "2026-03-31", "2026-03-31",
         "HRM（人事・労務・給与）",
         1, "G-HRM", 450, 0),

        # ── 新規業務アプリ APM-008〜APM-014 ──
        ("APM-008", "法務契約管理システム",            "法務部",         "running",
         "DocuSign Japan",
         "加藤 七子", "加藤 七子", "山田 太郎", "中村 五郎",
         "2020-07-01", "2020-07-15", "2028-06-30", None,
         "Legal / Compliance（法務・コンプライアンス）",
         3, None, 250, 0),

        ("APM-009", "マーケティング自動化ツール",      "マーケティング部", "running",
         "HubSpot Japan",
         "吉田 八郎", "吉田 八郎", "山田 太郎", "中村 五郎",
         "2021-10-01", "2021-11-01", "2028-09-30", None,
         "Marketing（マーケティング）",
         3, None, 350, 0),

        ("APM-010", "設備管理システム",                "製造部",         "running",
         "株式会社FACILITY",
         "松本 十郎", "松本 十郎", "山田 太郎", "中村 五郎",
         "2019-04-01", "2019-04-01", "2027-03-31", None,
         "ITSM / ITOM（ITサービス・運用管理）",
         2, None, 280, 0),

        ("APM-011", "品質管理システム",                "品質管理部",     "running",
         "株式会社QA-Pro",
         "小林 六子", "小林 六子", "山田 太郎", "中村 五郎",
         "2020-01-01", "2020-01-15", "2028-12-31", None,
         "Other（その他）",
         2, None, 310, 0),

        ("APM-012", "カスタマーサポートチケット管理",  "カスタマーサポート部", "running",
         "Zendesk Japan",
         "木村 梅子", "木村 梅子", "山田 太郎", "中村 五郎",
         "2021-07-01", "2021-07-01", "2029-06-30", None,
         "ITSM / ITOM（ITサービス・運用管理）",
         3, None, 240, 0),

        ("APM-013", "勤怠管理システム",                "人事部",         "running",
         "株式会社TIME-Pro",
         "田中 花子", "田中 花子", "山田 太郎", "中村 五郎",
         "2022-07-01", "2022-07-01", "2030-06-30", None,
         "HRM（人事・労務・給与）",
         2, None, 190, 0),

        ("APM-014", "社内ポータル",                    "総務部",         "running",
         "Microsoft",
         "渡辺 四郎", "渡辺 四郎", "山田 太郎", "中村 五郎",
         "2018-04-01", "2018-04-01", "2028-03-31", None,
         "Collaboration（グループウェア・社内コミュニケーション）",
         2, None, 180, 0),

        # ── エリア①追加：廃止予定システム（APM-015〜APM-022） ──
        ("APM-015", "旧勤怠管理システム",              "人事部",         "retire",
         "株式会社レガシーHR",
         "田中 花子", "退任", "退任", "退任",
         "2008-04-01", "2008-04-01", "2025-03-31", "2025-03-31",
         "HRM（人事・労務・給与）",
         1, "APM-013", 280, 0),

        ("APM-016", "レガシー帳票出力システム",         "情報システム部", "running",
         "株式会社帳票SI",
         "山田 太郎", "山田 太郎", "山田 太郎", "退任",
         "2007-10-01", "2007-10-01", "2026-03-31", None,
         "Document Management（文書・コンテンツ管理）",
         1, None, 120, 0),

        ("APM-017", "旧会議室予約システム",             "総務部",         "running",
         "株式会社オフィスSI",
         "渡辺 四郎", "渡辺 四郎", "渡辺 四郎", "退任",
         "2011-04-01", "2011-04-01", "2026-06-30", None,
         "Collaboration（グループウェア・社内コミュニケーション）",
         1, None, 80, 0),

        ("APM-018", "旧社内チャットツール",             "総務部",         "retire",
         "旧ベンダー（サービス終了）",
         "渡辺 四郎", "退任", "退任", "退任",
         "2013-07-01", "2013-07-01", "2025-09-30", "2025-09-30",
         "Communication Platform（社内コミュニケーション）",
         1, "APM-014", 150, 0),

        ("APM-019", "旧文書管理システム",               "総務部",         "running",
         "株式会社文書SI",
         "渡辺 四郎", "渡辺 四郎", "山田 太郎", "退任",
         "2010-04-01", "2010-04-01", "2026-09-30", None,
         "Document Management（文書・コンテンツ管理）",
         1, "APM-006", 320, 0),

        ("APM-020", "旧経費精算ワークフロー",           "経理部",         "running",
         "株式会社レガシーFinance",
         "鈴木 一郎", "鈴木 一郎", "山田 太郎", "退任",
         "2009-10-01", "2009-10-01", "2026-03-31", None,
         "Finance（経理・財務・予算）",
         1, "G-ERP", 480, 0),

        ("APM-021", "旧勤怠連携バッチシステム",         "情報システム部", "running",
         "内製",
         "山田 太郎", "山田 太郎", "山田 太郎", "山田 太郎",
         "2012-04-01", "2012-04-01", "2026-06-30", None,
         "ITSM / ITOM（ITサービス・運用管理）",
         1, "APM-013", 60, 1),

        ("APM-022", "旧グループウェア",                 "総務部",         "running",
         "旧ベンダー",
         "渡辺 四郎", "渡辺 四郎", "山田 太郎", "退任",
         "2006-04-01", "2006-04-01", "2026-12-31", None,
         "Collaboration（グループウェア・社内コミュニケーション）",
         1, "APM-014", 550, 0),
    ]

    for (app_id, name, dept, status, vendor,
         biz, sys_o, ops, dev,
         start_p, start_a, end_p, end_a, app_cat,
         portfolio_area, migration_target_id, annual_cost, is_infra) in apps:
        cur.execute(
            """
            INSERT INTO application
                (application_id, application_name, owner_department_id, status, vendor,
                 business_owner, system_owner, ops_manager, dev_manager,
                 start_plan, start_actual, end_plan, end_actual, app_category,
                 portfolio_area, migration_target_id, annual_cost_million, is_infrastructure)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [app_id, name, dept_ids[dept], status, vendor,
             biz, sys_o, ops, dev,
             start_p, start_a, end_p, end_a, app_cat,
             portfolio_area, migration_target_id, annual_cost, is_infra],
        )

    # ---------- 依存関係（28件） ----------
    deps = [
        # オンプレ系業務アプリ → 国内インフラ
        ("APM-001", "INF-DC1",  "infra", "東京DCオンプレサーバー上で稼働"),
        ("APM-001", "INF-AUTH", "auth",  "社内認証基盤でSSO連携"),
        ("APM-003", "INF-DC1",  "infra", "大阪DCオンプレサーバー上で稼働"),
        ("APM-003", "INF-AUTH", "auth",  "社内認証基盤でSSO連携"),
        ("APM-007", "INF-DC1",  "infra", "東京DCオンプレサーバー上で稼働（廃止済）"),
        ("APM-007", "G-HRM",    "data",  "G-HRMへ人事データ移行完了"),
        ("APM-010", "INF-DC1",  "infra", "東京DCオンプレサーバー上で稼働"),
        ("APM-011", "INF-DC1",  "infra", "大阪DCオンプレサーバー上で稼働"),
        # クラウド系業務アプリ → G-CLOUD / G-SSO
        ("APM-002", "G-CLOUD",  "infra", "AWS上でホスティング"),
        ("APM-002", "G-SSO",    "auth",  "グローバルSSO連携"),
        ("APM-004", "G-CLOUD",  "infra", "AWS上でホスティング"),
        ("APM-004", "G-SSO",    "auth",  "グローバルSSO連携"),
        ("APM-005", "G-CLOUD",  "infra", "AWS上で開発中"),
        ("APM-005", "G-SSO",    "auth",  "グローバルSSO連携"),
        ("APM-006", "G-CLOUD",  "infra", "AWS上で構築予定"),
        ("APM-008", "G-CLOUD",  "infra", "AWS上でホスティング"),
        ("APM-008", "G-SSO",    "auth",  "グローバルSSO連携"),
        ("APM-009", "G-SSO",    "auth",  "グローバルSSO連携"),
        ("APM-012", "G-CLOUD",  "infra", "AWS上でホスティング"),
        ("APM-013", "G-CLOUD",  "infra", "SaaS連携（KING OF TIME）"),
        ("APM-013", "G-SSO",    "auth",  "グローバルSSO連携"),
        ("APM-014", "G-CLOUD",  "infra", "SharePoint Online（M365 / AWS連携）"),
        ("APM-014", "G-SSO",    "auth",  "グローバルSSO連携"),
        # インフラ間移行依存
        ("INF-DC1", "G-CLOUD",  "infra", "AWSへ段階移行中"),
        ("INF-AUTH","G-SSO",    "auth",  "G-SSO移行進行中"),
        # グローバル基盤
        ("G-ERP",   "G-CLOUD",  "infra", "AWS上で稼働"),
        ("G-ERP",   "G-SSO",    "auth",  "グローバルSSO連携"),
        ("G-HRM",   "G-CLOUD",  "infra", "AWS上で開発中"),
        # エリア①廃止予定システム → 国内インフラ依存
        ("APM-015", "INF-DC1",  "infra", "東京DCオンプレサーバー上で稼働（廃止済）"),
        ("APM-016", "INF-DC1",  "infra", "東京DCオンプレ帳票サーバー上で稼働"),
        ("APM-020", "INF-DC1",  "infra", "東京DCオンプレサーバー上で稼働（廃止予定）"),
        ("APM-021", "INF-DC1",  "infra", "東京DCオンプレバッチサーバー上で稼働"),
        ("APM-022", "INF-AUTH", "auth",  "旧社内認証基盤でSSO連携（廃止予定）"),
    ]
    for app_id, dep_id, dep_type, note in deps:
        cur.execute(
            """INSERT INTO application_dependency
                   (app_id, depends_on_app_id, dependency_type, note)
               VALUES (?, ?, ?, ?)""",
            [app_id, dep_id, dep_type, note],
        )

    # ---------- 環境（30件） ----------
    # (app_id, env_type, location, ip, host, os, middleware, cpu_mem, storage)
    envs = [
        # ── グローバル基盤 ──
        ("G-CLOUD", "本番環境",        "AWS ap-northeast-1",    "VPC 10.10.0.0/16",  "aws-prod.corp.local",        "Amazon Linux 2023", "Kubernetes 1.30",        "多数 EC2 インスタンス", "S3/EBS/RDS"),
        ("G-CLOUD", "DR環境",           "AWS ap-northeast-3",    "VPC 10.20.0.0/16",  "aws-dr.corp.local",           "Amazon Linux 2023", "Kubernetes 1.30",        "多数 EC2 インスタンス", "S3/EBS"),
        ("G-SSO",   "本番環境",         "Azure Japan East",      "40.79.192.0/24",    "sso-prod.corp.local",         "Azure AD",          "Microsoft Entra ID",     "マネージドサービス",    "Azure ストレージ"),
        ("G-ERP",   "本番環境",         "AWS ap-northeast-1",    "VPC 10.30.0.0/16",  "erp-prod.corp.local",         "SUSE Linux 15",     "SAP S/4HANA 2023",       "16vCPU/128GB",          "10TB SSD"),
        ("G-HRM",   "開発環境",         "Workday Sandbox",       "SaaS",              "hrm-dev.corp.local",          "SaaS (Workday)",     "Workday Sandbox",        "マネージドサービス",    "SaaS ストレージ"),
        # ── 国内インフラ ──
        ("INF-DC1", "本番環境",         "東京DC（大手町）",       "10.0.0.0/16",       "dc1-tokyo.corp.local",        "VMware ESXi 7.0",   "VMware vCenter 7.0",     "160vCPU/1024GB（計）",  "NetApp AFF A400 100TB"),
        ("INF-DC1", "DR環境",           "大阪DC（本社内）",       "10.1.0.0/16",       "dc1-osaka.corp.local",        "VMware ESXi 7.0",   "VMware vCenter 7.0",     "80vCPU/512GB（計）",    "NetApp AFF A250 50TB"),
        ("INF-AUTH","本番環境",         "東京DC（大手町）",       "10.0.1.0/24",       "auth-prod.corp.local",        "Windows Server 2019","Active Directory DS",    "4vCPU/16GB",            "500GB SSD RAID1"),
        # ── 業務アプリ ──
        ("APM-001", "本番環境",         "東京DC（大手町）",       "10.0.2.10",         "hr-prod.corp.local",          "RHEL 8.6",          "Tomcat 10 / Java 17",    "8vCPU/32GB",            "1TB SSD"),
        ("APM-001", "ステージング環境",  "東京DC（大手町）",       "10.0.2.20",         "hr-stg.corp.local",           "RHEL 8.6",          "Tomcat 10 / Java 17",    "4vCPU/16GB",            "500GB SSD"),
        ("APM-001", "開発環境",         "AWS ap-northeast-1",    "172.31.1.10",       "hr-dev.corp.local",           "Amazon Linux 2",    "Tomcat 10 / Java 17",    "2vCPU/8GB",             "200GB SSD"),
        ("APM-002", "本番環境",         "AWS ap-northeast-1",    "52.2.10.10",        "sfa-prod.corp.local",         "Amazon Linux 2",    "Node.js 18 / PM2",       "4vCPU/16GB",            "500GB SSD"),
        ("APM-002", "テスト環境",        "AWS ap-northeast-1",    "52.2.11.10",        "sfa-test.corp.local",         "Amazon Linux 2",    "Node.js 18 / PM2",       "2vCPU/8GB",             "200GB SSD"),
        ("APM-003", "本番環境",         "大阪DC（本社内）",       "10.1.3.10",         "inv-prod.corp.local",         "CentOS 7.9",        "Apache / PHP 8.1",       "8vCPU/32GB",            "2TB HDD RAID5"),
        ("APM-003", "ステージング環境",  "大阪DC（本社内）",       "10.1.3.20",         "inv-stg.corp.local",          "CentOS 7.9",        "Apache / PHP 8.1",       "4vCPU/16GB",            "1TB HDD"),
        ("APM-004", "本番環境",         "AWS ap-northeast-1",    "52.3.10.10",        "expense-prod.corp.local",     "Amazon Linux 2",    "Python 3.11 / FastAPI",  "4vCPU/8GB",             "200GB SSD"),
        ("APM-004", "開発環境",         "AWS ap-northeast-1",    "172.31.3.10",       "expense-dev.corp.local",      "Amazon Linux 2",    "Python 3.11 / FastAPI",  "2vCPU/4GB",             "100GB SSD"),
        ("APM-005", "開発環境",         "AWS ap-northeast-1",    "172.31.5.10",       "crm-dev.corp.local",          "Amazon Linux 2",    "React / FastAPI",         "2vCPU/4GB",             "100GB SSD"),
        ("APM-007", "本番環境",         "東京DC（大手町）",       "10.0.7.10",         "payroll-old.corp.local",      "Windows Server 2012","COBOL / WebSphere 8",   "4vCPU/16GB",            "500GB HDD"),
        ("APM-008", "本番環境",         "AWS ap-northeast-1",    "52.8.10.10",        "legal-prod.corp.local",       "Amazon Linux 2",    "Java 11 / Spring Boot",  "4vCPU/8GB",             "200GB SSD"),
        ("APM-008", "STG環境",          "AWS ap-northeast-1",    "52.8.11.10",        "legal-stg.corp.local",        "Amazon Linux 2",    "Java 11 / Spring Boot",  "2vCPU/4GB",             "100GB SSD"),
        ("APM-009", "本番環境",         "SaaS (HubSpot)",        "SaaS",              "mktg.corp.local",             "SaaS",              "HubSpot Marketing Hub",  "マネージドサービス",    "SaaS ストレージ"),
        ("APM-010", "本番環境",         "東京DC（大手町）",       "10.0.10.10",        "fac-prod.corp.local",         "CentOS 7.9",        "Tomcat 9 / Java 11",     "4vCPU/16GB",            "1TB HDD"),
        ("APM-010", "テスト環境",        "東京DC（大手町）",       "10.0.10.20",        "fac-test.corp.local",         "CentOS 7.9",        "Tomcat 9 / Java 11",     "2vCPU/8GB",             "500GB HDD"),
        ("APM-011", "本番環境",         "大阪DC（本社内）",       "10.1.11.10",        "qa-prod.corp.local",          "RHEL 7.9",          "Python 3.9 / Django",    "4vCPU/16GB",            "1TB SSD"),
        ("APM-012", "本番環境",         "AWS ap-northeast-1",    "52.12.10.10",       "cs-prod.corp.local",          "Amazon Linux 2",    "Node.js 18 / PM2",       "4vCPU/8GB",             "200GB SSD"),
        ("APM-012", "STG環境",          "AWS ap-northeast-1",    "52.12.11.10",       "cs-stg.corp.local",           "Amazon Linux 2",    "Node.js 18 / PM2",       "2vCPU/4GB",             "100GB SSD"),
        ("APM-013", "本番環境",         "SaaS (KING OF TIME)",   "SaaS",              "attendance.corp.local",       "SaaS",              "KING OF TIME",           "マネージドサービス",    "SaaS ストレージ"),
        ("APM-014", "本番環境",         "SaaS (Microsoft 365)",  "SaaS",              "portal.corp.local",           "SaaS",              "SharePoint Online",      "マネージドサービス",    "SharePoint ストレージ"),
    ]
    env_ids: dict = {}
    has_env_id = cur.execute("SELECT relation_type_id FROM relation_type WHERE type_name='has_environment'").fetchone()[0]
    for row in envs:
        app_id, env_type = row[0], row[1]
        cur.execute(
            """INSERT INTO environment
                   (env_type, location, ip, host, os, middleware, cpu_mem, storage)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            list(row[1:]),
        )
        env_id = cur.lastrowid
        env_ids[(app_id, env_type)] = env_id
        cur.execute(
            """INSERT INTO cmdb_rel_ci
                   (parent_table, parent_id, child_table, child_id, relation_type_id)
               VALUES ('application', ?, 'environment', ?, ?)""",
            [app_id, str(env_id), has_env_id],
        )

    # ---------- 構成情報（CI, 41件） ----------
    def eid(app_id, env_type):
        return env_ids.get((app_id, env_type))

    # (env_id, ci_name, ci_type, hostname, ip_address, bmc_ip,
    #  os, os_version, cpu, memory, storage, vendor, model, status, note)
    ci_data = [
        # ── G-CLOUD ──
        (eid("G-CLOUD","本番環境"),  "aws-mgmt-prod",     "Other",   "aws-mgmt-prod.corp.local",    "VPC内",       None, None,None,None,None,None,"AWS","Management Console","active","AWS Organizations 管理アカウント"),
        (eid("G-CLOUD","DR環境"),    "aws-mgmt-dr",       "Other",   "aws-mgmt-dr.corp.local",      "VPC内",       None, None,None,None,None,None,"AWS","Management Console","active","DR リージョン管理コンソール"),
        # ── G-SSO ──
        (eid("G-SSO","本番環境"),    "azure-ad-tenant",   "Other",   "tenant.corp.onmicrosoft.com", "Azure",       None, None,None,None,None,None,"Microsoft","Entra ID P2","active","全社 SSO テナント / MFA 有効"),
        # ── G-ERP ──
        (eid("G-ERP","本番環境"),    "erp-ap-prod-01",    "Server",  "erp-ap-prod-01.corp.local",   "10.30.1.10",  "10.30.1.200","SUSE Linux 15","15 SP4","Intel Xeon Platinum 8380 2.3GHz 40C","256GB DDR4 ECC","2TB SSD RAID10","Fujitsu","PRIMERGY RX4770 M6","active","SAP アプリケーションサーバー"),
        (eid("G-ERP","本番環境"),    "erp-db-prod-01",    "DB",      "erp-db-prod-01.corp.local",   "10.30.1.11",  "10.30.1.201","SUSE Linux 15","15 SP4","Intel Xeon Platinum 8380 2.3GHz 40C","512GB DDR4 ECC","10TB SSD RAID10","Fujitsu","PRIMERGY RX4770 M6","active","SAP HANA DB (本番)"),
        # ── G-HRM ──
        (eid("G-HRM","開発環境"),    "hrm-sandbox-01",    "Other",   "hrm-sandbox.workday.com",     "SaaS",        None, None,None,None,None,None,"Workday","Workday HCM Sandbox","active","導入検証用 Sandbox テナント"),
        # ── INF-DC1 ──
        (eid("INF-DC1","本番環境"),  "dc1-vcenter-01",    "Server",  "dc1-vcenter-01.corp.local",   "10.0.0.10",   "10.0.0.200","Windows Server 2019","1809","Intel Xeon Gold 6254 3.1GHz 18C","64GB DDR4 ECC","500GB SSD","Dell","PowerEdge R740","active","vCenter Server 7.0 管理"),
        (eid("INF-DC1","本番環境"),  "dc1-core-sw-01",    "Network", "dc1-core-sw-01.corp.local",   "10.0.0.1",    "10.0.0.201",None,None,None,None,None,"Cisco","Catalyst 9500-48Y4C","active","コアスイッチ L3 / VLAN管理"),
        (eid("INF-DC1","DR環境"),    "dc1-vcenter-dr-01", "Server",  "dc1-vcenter-dr-01.corp.local","10.1.0.10",   "10.1.0.200","Windows Server 2019","1809","Intel Xeon Silver 4214R 2.4GHz 12C","32GB DDR4","300GB SSD","Dell","PowerEdge R640","active","DR vCenter Server 7.0"),
        # ── INF-AUTH ──
        (eid("INF-AUTH","本番環境"), "auth-dc01",         "Server",  "auth-dc01.corp.local",        "10.0.1.11",   "10.0.1.200","Windows Server 2019","1809","Intel Xeon Silver 4110 2.1GHz 8C","16GB DDR4 ECC","500GB SSD RAID1","HP","ProLiant DL380 Gen10","active","Active Directory DC1（FSMO保持）"),
        (eid("INF-AUTH","本番環境"), "auth-dc02",         "Server",  "auth-dc02.corp.local",        "10.0.1.12",   "10.0.1.201","Windows Server 2019","1809","Intel Xeon Silver 4110 2.1GHz 8C","16GB DDR4 ECC","500GB SSD RAID1","HP","ProLiant DL380 Gen10","active","Active Directory DC2（冗長）"),
        # ── APM-001 ──
        (eid("APM-001","本番環境"),  "hr-web-prod-01",    "Server",  "hr-web-prod-01.corp.local",   "10.0.2.11",   "10.0.2.200","RHEL 8.6","8.6.0","Intel Xeon Gold 6248R 3.0GHz 20C","32GB DDR4 ECC","500GB SSD","Dell","PowerEdge R650","active","APサーバー（Tomcat/Java）"),
        (eid("APM-001","本番環境"),  "hr-db-prod-01",     "DB",      "hr-db-prod-01.corp.local",    "10.0.2.12",   "10.0.2.201","RHEL 8.6","8.6.0","Intel Xeon Gold 6248R 3.0GHz 20C","64GB DDR4 ECC","2TB SSD RAID1","Dell","PowerEdge R650","active","PostgreSQL 15 マスター"),
        (eid("APM-001","本番環境"),  "hr-lb-prod-01",     "Network", "hr-lb-prod-01.corp.local",    "10.0.2.10",   "10.0.2.202",None,None,None,None,None,"F5","BIG-IP i2600","active","ロードバランサー VIP 10.0.2.10"),
        (eid("APM-001","ステージング環境"),"hr-web-stg-01","Server",  "hr-web-stg-01.corp.local",    "10.0.2.21",   "10.0.2.210","RHEL 8.6","8.6.0","Intel Xeon Silver 4214R 2.4GHz 12C","16GB DDR4","300GB SSD","Dell","PowerEdge R550","active","STG APサーバー"),
        (eid("APM-001","ステージング環境"),"hr-db-stg-01", "DB",      "hr-db-stg-01.corp.local",     "10.0.2.22",   "10.0.2.211","RHEL 8.6","8.6.0","Intel Xeon Silver 4214R 2.4GHz 12C","32GB DDR4","1TB SSD","Dell","PowerEdge R550","active","PostgreSQL 15 STG"),
        (eid("APM-001","開発環境"),  "hr-dev-ap-01",      "Server",  "hr-dev-ap-01.corp.local",     "172.31.1.11", None,"Amazon Linux 2","2","2vCPU (t3.medium)","4GB","100GB SSD","AWS","EC2 t3.medium","active","開発用 APサーバー"),
        # ── APM-002 ──
        (eid("APM-002","本番環境"),  "sfa-ap-prod-01",    "Server",  "sfa-ap-prod-01.corp.local",   "52.2.10.11",  None,"Amazon Linux 2","2","4vCPU (c6i.xlarge)","8GB","200GB SSD","AWS","EC2 c6i.xlarge","active","Node.js 18 / PM2 本番"),
        (eid("APM-002","本番環境"),  "sfa-db-prod-01",    "DB",      "sfa-db-prod-01.corp.local",   "52.2.10.12",  None,"Amazon Linux 2","2","2vCPU (db.r6g.large)","16GB","500GB SSD","AWS","RDS PostgreSQL 15 マルチAZ","active","RDS マルチAZ"),
        (eid("APM-002","テスト環境"),"sfa-ap-test-01",    "Server",  "sfa-ap-test-01.corp.local",   "52.2.11.11",  None,"Amazon Linux 2","2","2vCPU (t3.medium)","4GB","100GB SSD","AWS","EC2 t3.medium","active","テスト環境 APサーバー"),
        # ── APM-003 ──
        (eid("APM-003","本番環境"),  "inv-web-prod-01",   "Server",  "inv-web-prod-01.corp.local",  "10.1.3.11",   "10.1.3.200","CentOS 7.9","7.9.2009","Intel Xeon E5-2680v4 2.4GHz 14C","16GB DDR4","1TB HDD","Fujitsu","PRIMERGY RX2530 M4","active","Apache/PHP Webサーバー"),
        (eid("APM-003","本番環境"),  "inv-db-prod-01",    "DB",      "inv-db-prod-01.corp.local",   "10.1.3.12",   "10.1.3.201","CentOS 7.9","7.9.2009","Intel Xeon E5-2680v4 2.4GHz 14C","32GB DDR4","2TB HDD RAID5","Fujitsu","PRIMERGY RX2540 M4","active","MySQL 8.0 本番"),
        (eid("APM-003","ステージング環境"),"inv-web-stg-01","Server", "inv-web-stg-01.corp.local",   "10.1.3.21",   "10.1.3.210","CentOS 7.9","7.9.2009","Intel Xeon E5-2620v4 2.1GHz 8C","8GB DDR4","500GB HDD","Fujitsu","PRIMERGY RX2510 M2","active","STG Webサーバー"),
        # ── APM-004 ──
        (eid("APM-004","本番環境"),  "expense-ap-prod-01","Server",  "expense-ap-prod-01.corp.local","52.3.10.11",  None,"Amazon Linux 2","2","2vCPU (t3.large)","8GB","100GB SSD","AWS","EC2 t3.large","active","FastAPI 本番サーバー"),
        (eid("APM-004","本番環境"),  "expense-db-prod-01","DB",      "expense-db-prod-01.corp.local","52.3.10.12",  None,"Amazon Linux 2","2","2vCPU (db.t3.medium)","4GB","100GB SSD","AWS","RDS MySQL 8.0","active","RDS マルチAZ"),
        (eid("APM-004","開発環境"),  "expense-dev-ap-01", "Server",  "expense-dev-ap-01.corp.local","172.31.3.11", None,"Amazon Linux 2","2","1vCPU (t3.small)","2GB","50GB SSD","AWS","EC2 t3.small","active","開発用サーバー"),
        # ── APM-005 ──
        (eid("APM-005","開発環境"),  "crm-dev-ap-01",     "Server",  "crm-dev-ap-01.corp.local",    "172.31.5.11", None,"Amazon Linux 2","2","2vCPU (t3.medium)","4GB","50GB SSD","AWS","EC2 t3.medium","active","CRM 開発 APIサーバー"),
        # ── APM-007 (廃止済み) ──
        (eid("APM-007","本番環境"),  "payroll-ap-old-01", "Server",  "payroll-ap-old-01.corp.local","10.0.7.11",   "10.0.7.200","Windows Server 2012","R2","Intel Xeon E5-2650v2 2.6GHz 8C","16GB DDR3","300GB HDD","NEC","Express5800/R120g-1E","decommission","旧給与AP（廃止済）"),
        (eid("APM-007","本番環境"),  "payroll-db-old-01", "DB",      "payroll-db-old-01.corp.local","10.0.7.12",   "10.0.7.201","Windows Server 2012","R2","Intel Xeon E5-2650v2 2.6GHz 8C","32GB DDR3","1TB HDD RAID5","NEC","Express5800/R120g-2E","decommission","旧給与DB Oracle 11g（廃止済）"),
        # ── APM-008 ──
        (eid("APM-008","本番環境"),  "legal-ap-prod-01",  "Server",  "legal-ap-prod-01.corp.local", "52.8.10.11",  None,"Amazon Linux 2","2","2vCPU (t3.large)","8GB","200GB SSD","AWS","EC2 t3.large","active","Spring Boot 本番 APサーバー"),
        (eid("APM-008","本番環境"),  "legal-db-prod-01",  "DB",      "legal-db-prod-01.corp.local", "52.8.10.12",  None,"Amazon Linux 2","2","2vCPU (db.t3.large)","8GB","500GB SSD","AWS","RDS PostgreSQL 15","active","RDS マルチAZ"),
        (eid("APM-008","STG環境"),   "legal-ap-stg-01",   "Server",  "legal-ap-stg-01.corp.local",  "52.8.11.11",  None,"Amazon Linux 2","2","1vCPU (t3.medium)","4GB","100GB SSD","AWS","EC2 t3.medium","active","STG APサーバー"),
        # ── APM-009 ──
        (eid("APM-009","本番環境"),  "hubspot-tenant",    "Other",   "corp.hubspot.com",            "SaaS",        None,None,None,None,None,None,"HubSpot","Marketing Hub Professional","active","全社 HubSpot テナント"),
        # ── APM-010 ──
        (eid("APM-010","本番環境"),  "fac-ap-prod-01",    "Server",  "fac-ap-prod-01.corp.local",   "10.0.10.11",  "10.0.10.200","CentOS 7.9","7.9.2009","Intel Xeon E5-2620v4 2.1GHz 8C","16GB DDR4","500GB HDD","NEC","Express5800/R110j-1","active","設備管理 APサーバー"),
        (eid("APM-010","本番環境"),  "fac-db-prod-01",    "DB",      "fac-db-prod-01.corp.local",   "10.0.10.12",  "10.0.10.201","CentOS 7.9","7.9.2009","Intel Xeon E5-2620v4 2.1GHz 8C","16GB DDR4","1TB HDD RAID1","NEC","Express5800/R120g-1E","active","MySQL 8.0 本番"),
        # ── APM-011 ──
        (eid("APM-011","本番環境"),  "qa-ap-prod-01",     "Server",  "qa-ap-prod-01.corp.local",    "10.1.11.11",  "10.1.11.200","RHEL 7.9","7.9","Intel Xeon E5-2680v4 2.4GHz 14C","16GB DDR4","500GB SSD","Fujitsu","PRIMERGY RX2530 M4","active","品質管理 APサーバー"),
        (eid("APM-011","本番環境"),  "qa-db-prod-01",     "DB",      "qa-db-prod-01.corp.local",    "10.1.11.12",  "10.1.11.201","RHEL 7.9","7.9","Intel Xeon E5-2680v4 2.4GHz 14C","32GB DDR4","1TB SSD RAID1","Fujitsu","PRIMERGY RX2540 M4","active","PostgreSQL 14 本番"),
        # ── APM-012 ──
        (eid("APM-012","本番環境"),  "cs-ap-prod-01",     "Server",  "cs-ap-prod-01.corp.local",    "52.12.10.11", None,"Amazon Linux 2","2","2vCPU (t3.large)","8GB","200GB SSD","AWS","EC2 t3.large","active","Zendesk API連携サーバー"),
        (eid("APM-012","本番環境"),  "cs-db-prod-01",     "DB",      "cs-db-prod-01.corp.local",    "52.12.10.12", None,"Amazon Linux 2","2","2vCPU (db.t3.medium)","4GB","100GB SSD","AWS","RDS MySQL 8.0","active","チケット分析用 DB"),
        (eid("APM-012","STG環境"),   "cs-ap-stg-01",      "Server",  "cs-ap-stg-01.corp.local",     "52.12.11.11", None,"Amazon Linux 2","2","1vCPU (t3.small)","2GB","50GB SSD","AWS","EC2 t3.small","active","STG APサーバー"),
        # ── APM-013 ──
        (eid("APM-013","本番環境"),  "kot-tenant",        "Other",   "corp.kingofTime.jp",          "SaaS",        None,None,None,None,None,None,"株式会社ヒューマンテクノロジーズ","KING OF TIME","active","全社勤怠管理テナント"),
        # ── APM-014 ──
        (eid("APM-014","本番環境"),  "sharepoint-tenant", "Other",   "corp.sharepoint.com",         "SaaS",        None,None,None,None,None,None,"Microsoft","SharePoint Online (M365 E3)","active","全社ポータル / Teams連携"),
    ]
    has_ci_id = cur.execute("SELECT relation_type_id FROM relation_type WHERE type_name='has_ci'").fetchone()[0]
    for (env_id, ci_name, ci_type, hostname, ip_address, bmc_ip,
         os_, os_version, cpu, memory, storage, vendor, model, status, note) in ci_data:
        if env_id is None:
            continue
        cur.execute(
            """INSERT INTO configuration_item
                   (ci_name, ci_type, hostname, ip_address, bmc_ip,
                    os, os_version, cpu, memory, storage, vendor, model, status, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [ci_name, ci_type, hostname, ip_address, bmc_ip,
             os_, os_version, cpu, memory, storage, vendor, model, status, note],
        )
        ci_id = cur.lastrowid
        cur.execute(
            """INSERT INTO cmdb_rel_ci
                   (parent_table, parent_id, child_table, child_id, relation_type_id)
               VALUES ('environment', ?, 'configuration_item', ?, ?)""",
            [str(env_id), str(ci_id), has_ci_id],
        )

    # ---------- 申請（20件） ----------
    def _chg(*items):
        return json.dumps([{"label": l, "field": f, "before": b, "after": a}
                           for l, f, b, a in items], ensure_ascii=False)

    u = user_ids  # 短縮エイリアス
    requests = [
        # ── 新規登録 (register) 7件 ──
        {"request_id": "REQ-001", "type": "register", "application_id": "APM-008",
         "applicant_user_id": u["加藤 七子"], "applied_at": "2024-06-01 10:00", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2024-06-05 14:00",
         "reason": "法務部の契約書管理をデジタル化するため DocuSign を導入する",
         "changes": None, "app_name": "法務契約管理システム", "dept": "法務部",
         "biz_owner": "加藤 七子", "new_status": "running", "start_plan": "2020-07-01", "end_plan": None},
        {"request_id": "REQ-002", "type": "register", "application_id": "APM-009",
         "applicant_user_id": u["吉田 八郎"], "applied_at": "2024-07-15 11:30", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2024-07-20 09:00",
         "reason": "リードナーチャリング自動化のため HubSpot を導入する",
         "changes": None, "app_name": "マーケティング自動化ツール", "dept": "マーケティング部",
         "biz_owner": "吉田 八郎", "new_status": "running", "start_plan": "2021-10-01", "end_plan": None},
        {"request_id": "REQ-003", "type": "register", "application_id": "APM-010",
         "applicant_user_id": u["松本 十郎"], "applied_at": "2024-04-01 09:00", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2024-04-10 11:00",
         "reason": "製造設備の予防保全強化のため設備管理システムを導入する",
         "changes": None, "app_name": "設備管理システム", "dept": "製造部",
         "biz_owner": "松本 十郎", "new_status": "running", "start_plan": "2019-04-01", "end_plan": None},
        {"request_id": "REQ-004", "type": "register", "application_id": "APM-011",
         "applicant_user_id": u["小林 六子"], "applied_at": "2024-09-01 10:00", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2024-09-08 15:00",
         "reason": "品質データのリアルタイム可視化により不良品追跡を迅速化する",
         "changes": None, "app_name": "品質管理システム", "dept": "品質管理部",
         "biz_owner": "小林 六子", "new_status": "running", "start_plan": "2020-01-01", "end_plan": None},
        {"request_id": "REQ-005", "type": "register", "application_id": "APM-012",
         "applicant_user_id": u["木村 梅子"], "applied_at": "2025-01-10 13:00", "status": "approved",
         "approver_user_id": u["加藤 七子"], "approved_at": "2025-01-15 10:00",
         "reason": "問い合わせ対応の一元管理によりSLA遵守率を向上させる",
         "changes": None, "app_name": "カスタマーサポートチケット管理", "dept": "カスタマーサポート部",
         "biz_owner": "木村 梅子", "new_status": "running", "start_plan": "2021-07-01", "end_plan": None},
        {"request_id": "REQ-006", "type": "register", "application_id": None,
         "applicant_user_id": u["渡辺 四郎"], "applied_at": "2026-03-01 10:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "全社の会議室予約を一元管理し二重予約をゼロにする",
         "changes": None, "app_name": "会議室予約システム", "dept": "総務部",
         "biz_owner": "渡辺 四郎", "new_status": "plan", "start_plan": "2026-10-01", "end_plan": None},
        {"request_id": "REQ-007", "type": "register", "application_id": None,
         "applicant_user_id": u["田中 花子"], "applied_at": "2026-04-05 14:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "eラーニングと研修管理を統合し必須研修受講率を100%にする",
         "changes": None, "app_name": "研修管理システム", "dept": "研修部",
         "biz_owner": "田中 花子", "new_status": "plan", "start_plan": "2027-04-01", "end_plan": None},
        # ── 変更申請 (update) 7件 ──
        {"request_id": "REQ-008", "type": "update", "application_id": "APM-001",
         "applicant_user_id": u["田中 花子"], "applied_at": "2025-04-10 09:00", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2025-04-12 11:00",
         "reason": "人事部長交代に伴うビジネスオーナー変更",
         "changes": _chg(("ビジネスオーナー", "business_owner", "山田 部長", "田中 花子")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-009", "type": "update", "application_id": "APM-002",
         "applicant_user_id": u["高橋 二郎"], "applied_at": "2025-05-01 10:30", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2025-05-07 09:00",
         "reason": "Salesforce ライセンス更新交渉によりサポート期限を2年延長",
         "changes": _chg(("廃止予定日", "end_plan", "2027-09-30", "2029-09-30")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-010", "type": "update", "application_id": "APM-003",
         "applicant_user_id": u["伊藤 三郎"], "applied_at": "2026-01-20 11:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "購買部長交代に伴うビジネスオーナー変更申請",
         "changes": _chg(("ビジネスオーナー", "business_owner", "伊藤 旧部長", "伊藤 三郎")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-011", "type": "update", "application_id": "APM-004",
         "applicant_user_id": u["鈴木 一郎"], "applied_at": "2025-03-10 14:00", "status": "rejected",
         "approver_user_id": u["清水 松子"], "approved_at": "2025-03-12 10:00",
         "reason": "経費精算システムのステータスを dev に変更申請",
         "changes": _chg(("ステータス", "status", "running", "dev")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-012", "type": "update", "application_id": "APM-008",
         "applicant_user_id": u["加藤 七子"], "applied_at": "2026-02-14 09:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "DocuSign ライセンス延長交渉のため廃止予定日を2年延長",
         "changes": _chg(("廃止予定日", "end_plan", "2028-06-30", "2030-06-30")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-013", "type": "update", "application_id": "APM-013",
         "applicant_user_id": u["田中 花子"], "applied_at": "2025-08-01 10:00", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2025-08-05 11:00",
         "reason": "勤怠管理担当変更によるシステムオーナー更新",
         "changes": _chg(("システムオーナー", "system_owner", "旧担当者", "田中 花子")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        {"request_id": "REQ-014", "type": "update", "application_id": "APM-014",
         "applicant_user_id": u["渡辺 四郎"], "applied_at": "2026-03-15 13:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "Microsoft 365 契約更新に伴い廃止予定日を延長",
         "changes": _chg(("廃止予定日", "end_plan", "2028-03-31", "2031-03-31")),
         "app_name": None, "dept": None, "biz_owner": None, "new_status": None, "start_plan": None, "end_plan": None},
        # ── 廃止申請 (retire) 6件 ──
        {"request_id": "REQ-015", "type": "retire", "application_id": "APM-007",
         "applicant_user_id": u["田中 花子"], "applied_at": "2025-05-20 16:40", "status": "approved",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2025-05-21 10:00",
         "reason": "G-HRM への移行完了のため旧給与計算システムを廃止する",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2026-03-31"},
        {"request_id": "REQ-016", "type": "retire", "application_id": "APM-005",
         "applicant_user_id": u["高橋 二郎"], "applied_at": "2025-09-01 10:00", "status": "rejected",
         "approver_user_id": u["佐藤 事務局"], "approved_at": "2025-09-03 14:00",
         "reason": "CRM 開発中断のため廃止申請",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2025-12-31"},
        {"request_id": "REQ-017", "type": "retire", "application_id": "APM-006",
         "applicant_user_id": u["渡辺 四郎"], "applied_at": "2026-02-28 10:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "文書管理は社内ポータル（APM-014）に統合するため別途申請計画を廃止",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2026-09-30"},
        {"request_id": "REQ-018", "type": "retire", "application_id": "APM-003",
         "applicant_user_id": u["伊藤 三郎"], "applied_at": "2025-11-10 09:00", "status": "rejected",
         "approver_user_id": u["清水 松子"], "approved_at": "2025-11-12 10:00",
         "reason": "在庫管理システムをグローバルシステムへ移行するため廃止申請",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2026-06-30"},
        {"request_id": "REQ-019", "type": "retire", "application_id": "APM-010",
         "applicant_user_id": u["松本 十郎"], "applied_at": "2026-03-20 11:00", "status": "pending",
         "approver_user_id": None, "approved_at": None,
         "reason": "設備管理システムを新IoT基盤に移行するための廃止申請",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2027-03-31"},
        {"request_id": "REQ-020", "type": "retire", "application_id": "APM-011",
         "applicant_user_id": u["小林 六子"], "applied_at": "2025-12-01 10:00", "status": "approved",
         "approver_user_id": u["加藤 七子"], "approved_at": "2025-12-05 11:00",
         "reason": "品質管理システムを刷新版へ移行完了のため旧システムを廃止する",
         "changes": None, "app_name": None, "dept": None, "biz_owner": None,
         "new_status": None, "start_plan": None, "end_plan": "2025-12-31"},
    ]
    for r in requests:
        cur.execute(
            """INSERT INTO apm_request
                   (request_id, type, application_id, applicant_user_id, applied_at, status,
                    approver_user_id, approved_at, reason, changes,
                    app_name, dept, biz_owner, new_status, start_plan, end_plan)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [r["request_id"], r["type"], r["application_id"],
             r["applicant_user_id"], r["applied_at"], r["status"],
             r["approver_user_id"], r["approved_at"], r["reason"], r["changes"],
             r["app_name"], r["dept"], r["biz_owner"],
             r["new_status"], r["start_plan"], r["end_plan"]],
        )

    # ---------- デマンド（20件） ----------
    def _d(did, title, it_class, cat, domain, dtype, start, due,
           subm, dept_name, mgr, sysown, pm,
           desc, portfolio, prog, chg_type, purpose,
           feas, prio, region, company, bunit,
           bcase, benefit, target, est, budget, cnote, notes,
           stage, rej=None, rev=None, appr=None):
        return dict(
            demand_id=did, title=title, it_class=it_class, category=cat, domain=domain, type=dtype,
            start_date=start, due_date=due,
            submitter_user_id=subm, department_id=dept_ids[dept_name],
            manager_user_id=mgr, system_owner_user_id=sysown, pm_user_id=pm,
            description=desc, portfolio=portfolio, program=prog, change_type=chg_type, purpose=purpose,
            feasibility=feas, priority=prio, region=region, company=company, business_unit=bunit,
            business_case=bcase, expected_benefit=benefit,
            target_date=target, estimated_cost=est, requested_budget=budget,
            cost_note=cnote, notes=notes, stage=stage,
            reject_reason=rej, review_comment=rev, approval_comment=appr,
        )

    demands = [
        # ── completed (3件) ──
        _d("DMND1001001", "営業支援CRM導入（国内営業部門）",
           "部門固有", "業務改善", "営業・マーケティング", "新規導入",
           "2025-04-01", "2026-03-31",
           u["高橋 二郎"], "営業本部", u["佐藤 事務局"], u["高橋 二郎"], u["山田 太郎"],
           "Salesforceを導入し、国内営業部門の顧客・商談管理を一元化する。",
           "営業IT", "営業DXプログラム", "新規", "商談情報の一元管理と営業活動の可視化",
           "A:確実", "2 - 高", "国内", "本社", "営業本部",
           "Excel・メール管理の非効率を解消。Salesforceで商談・予実管理を実現。",
           "受注率10%向上。週次レポート作成工数を2時間→0に削減。",
           "2026-04-01", 8_000_000, 10_000_000, "Salesforceライセンス5M/年、カスタマイズ3M",
           "全タスク完了済み。プロジェクト化済み。",
           "completed", None, "全審査項目クリア。", "承認。プロジェクト化を指示。"),

        _d("DMND1001002", "経費精算システム刷新",
           "全社共通", "インフラ刷新", "会計・財務", "更改・移行",
           "2024-10-01", "2025-09-30",
           u["鈴木 一郎"], "経理部", u["佐藤 事務局"], u["鈴木 一郎"], u["山田 太郎"],
           "老朽化した経費精算システムをクラウドSaaSへ移行し、承認フローのデジタル化を完了する。",
           "コーポレートIT", "業務効率化プログラム", "更改", "承認フロー完全デジタル化と紙廃止",
           "A:確実", "2 - 高", "国内", "本社", "経理部",
           "紙・FAXによる経費精算プロセスを全廃。SaaS移行で月次締め処理を2日短縮。",
           "月次締め2日短縮、年間コスト20%削減（紙・郵送費含む）。",
           "2025-10-01", 6_000_000, 8_000_000, "SaaSライセンス3M/年、移行費3M",
           "移行完了。旧システム廃止済み。",
           "completed", None, "コスト・セキュリティ審査全クリア。", "承認。速やかに実施のこと。"),

        _d("DMND1001003", "勤怠管理システム刷新（クラウド移行）",
           "全社共通", "インフラ刷新", "人事・労務", "更改・移行",
           "2024-04-01", "2025-03-31",
           u["田中 花子"], "人事部", u["佐藤 事務局"], u["田中 花子"], u["山田 太郎"],
           "オンプレ勤怠管理システムをクラウドサービス（TIME-Pro）へ移行し、在宅勤務対応を強化する。",
           "コーポレートIT", "テレワーク対応プログラム", "更改", "在宅勤務・フレックス対応の強化",
           "A:確実", "1 - 最重要", "国内", "本社", "人事部",
           "コロナ禍でのテレワーク拡大に対応するためクラウド化が急務。",
           "在宅勤務申請の自動集計。管理者工数を月10時間削減。",
           "2025-04-01", 5_000_000, 7_000_000, "TIME-Proライセンス2M/年、移行費3M",
           "移行完了。旧システム廃止済み。",
           "completed", None, "全審査通過。", "承認済み。計画通りに実施。"),

        # ── approved (3件) ──
        _d("DMND1001004", "グローバルERP統合推進",
           "グローバル展開", "インフラ刷新", "調達・購買", "更改・移行",
           "2026-04-01", "2028-09-30",
           u["伊藤 三郎"], "購買部", u["佐藤 事務局"], u["伊藤 三郎"], u["中村 五郎"],
           "12拠点で乱立するERPシステムをSAP S/4HANAに統合し、グローバル購買プロセスを標準化する。",
           "グローバルERP", "グローバルSCM刷新プログラム", "更改", "購買プロセス標準化とコスト削減",
           "B:高い", "1 - 最重要", "グローバル", "グループ全社", "購買部",
           "12拠点のERP乱立で年間運用コスト3億円超。SAP統合で30%削減見込み。",
           "年間運用コスト約1億円削減。調達リードタイム20%短縮。",
           "2028-10-01", 200_000_000, 250_000_000, "SAP S/4HANAライセンス100M、移行費100M、トレーニング50M",
           "海外拠点の合意取得済み。法務・コンプライアンス確認完了。プロジェクト化準備中。",
           "approved", None, "全審査クリア。投資委員会承認済み。", "承認。PM体制を早急に確立のこと。"),

        _d("DMND1001005", "品質管理システム刷新",
           "部門固有", "業務改善", "製造・品質", "更改・移行",
           "2026-01-01", "2026-12-31",
           u["小林 六子"], "品質管理部", u["佐藤 事務局"], u["小林 六子"], u["山田 太郎"],
           "旧来の紙ベース品質管理をシステム化し、不良品トレーサビリティとリアルタイム分析を実現する。",
           "製造IT", "製造DXプログラム", "更改", "品質データのリアルタイム可視化と不良品追跡迅速化",
           "A:確実", "2 - 高", "国内", "本社", "品質管理部",
           "紙台帳での管理では不良品発生から報告まで最大3日かかる。システム化でリアルタイム化。",
           "不良品検出速度を3日→1時間に短縮。クレーム対応コスト30%削減。",
           "2027-01-01", 15_000_000, 18_000_000, "SaaS品質管理ツールライセンス8M/年、導入費7M",
           "現行システムAPM-011の廃止と新システム導入を同時実施。",
           "approved", None, "技術審査・投資審査通過。", "承認。2026年内の稼働を厳守。"),

        _d("DMND1001006", "法務契約管理システム強化（電子契約対応）",
           "部門固有", "コンプライアンス", "法務・契約", "機能強化",
           "2026-04-01", "2026-09-30",
           u["加藤 七子"], "法務部", u["佐藤 事務局"], u["加藤 七子"], u["清水 松子"],
           "DocuSign（APM-008）に電子契約機能を追加し、契約書締結をペーパーレス化する。",
           "コーポレートIT", "ペーパーレス推進プログラム", "機能追加", "契約書締結の完全電子化",
           "A:確実", "2 - 高", "国内", "本社", "法務部",
           "年間約3000件の契約書の印刷・郵送コストが年間500万円。電子化で全廃可能。",
           "印刷・郵送コスト年間500万円を削減。契約締結リードタイムを14日→2日に短縮。",
           "2026-10-01", 5_000_000, 6_000_000, "DocuSign追加ライセンス2M、設定費3M",
           "取引先への電子契約同意取得が前提。法務部で事前確認済み。",
           "approved", None, "セキュリティ・コンプライアンス審査通過。", "承認。取引先対応を速やかに進めること。"),

        # ── qualified (3件) ──
        _d("DMND1001007", "AIチャットボット導入（社内問い合わせ対応）",
           "全社共通", "戦略投資", "総務・コーポレート", "新規導入",
           "2026-10-01", "2027-06-30",
           u["渡辺 四郎"], "総務部", u["佐藤 事務局"], u["渡辺 四郎"], u["中村 五郎"],
           "AIチャットボットを導入し、社内問い合わせ（IT・人事・総務）の一次対応を自動化する。",
           "コーポレートIT", "AI活用推進プログラム", "新規", "問い合わせ対応工数の削減とリードタイム短縮",
           "B:高い", "2 - 高", "国内", "本社", "総務部",
           "IT・人事・総務への月間問い合わせ件数は約1500件。チャットボットで60%の自動解決を目指す。",
           "月間工数200時間削減。問い合わせ解決平均時間を24時間→1時間に短縮。",
           "2027-07-01", 12_000_000, 15_000_000, "LLMサービス利用料4M/年、開発費8M、FAQデータ整備3M",
           "FAQデータベースの整備が前提条件。各部門との協力体制を構築中。",
           "qualified", None, "セキュリティ・アーキテクチャ審査完了。投資審査中。", None),

        _d("DMND1001008", "データ分析基盤整備（Data Lake構築）",
           "全社共通", "戦略投資", "IT基盤", "新規導入",
           "2026-07-01", "2027-09-30",
           u["中村 五郎"], "開発部", u["佐藤 事務局"], u["山田 太郎"], u["中村 五郎"],
           "AWS上にData Lakeを構築し、各業務システムのデータを統合・分析できる基盤を整備する。",
           "ITインフラ", "データ活用推進プログラム", "新規", "全社データの統合管理と分析基盤の確立",
           "B:高い", "1 - 最重要", "国内", "本社", "開発部",
           "各システムのデータがサイロ化しており、横断分析に毎回大量の手作業が必要。",
           "レポート作成工数を月40時間削減。経営意思決定スピード向上。",
           "2027-10-01", 30_000_000, 35_000_000, "AWSインフラ10M/年、構築費20M、運用費5M/年",
           "G-CLOUDのIAM整備が前提。セキュリティポリシー改定が必要。",
           "qualified", None, "技術審査完了。コスト精査中。", None),

        _d("DMND1001009", "マーケティング自動化強化（MA高度化）",
           "部門固有", "業務改善", "営業・マーケティング", "機能強化",
           "2026-08-01", "2027-03-31",
           u["吉田 八郎"], "マーケティング部", u["佐藤 事務局"], u["吉田 八郎"], u["山田 太郎"],
           "HubSpot（APM-009）の機能を高度化し、Salesforce（APM-002）とのリアルタイム連携を構築する。",
           "営業IT", "営業DXプログラム", "機能追加", "リードからクローズまでのデータ連携完全自動化",
           "A:確実", "2 - 高", "国内", "本社", "マーケティング部",
           "MAとCRMのデータ連携が手動のため、リード情報の同期に毎日2時間かかる。",
           "リード同期工数を年間500時間削減。コンバージョン率15%向上見込み。",
           "2027-04-01", 8_000_000, 10_000_000, "HubSpot追加ライセンス3M、連携開発5M",
           "Salesforceのカスタムオブジェクト追加が必要。営業本部との調整済み。",
           "qualified", None, "セキュリティ・アーキテクチャ審査完了。", None),

        # ── screening (3件) ──
        _d("DMND1001010", "全社工数管理ツール導入",
           "全社共通", "業務改善", "人事・労務", "新規導入",
           "2026-07-01", "2027-03-31",
           u["山田 太郎"], "情報システム部", u["佐藤 事務局"], u["山田 太郎"], u["鈴木 一郎"],
           "全社工数管理ツールを導入し、プロジェクト別・部門別の工数可視化と集計自動化を実現する。",
           "コーポレートIT", "生産性向上プログラム", "新規", "月次工数集計工数の削減と正確性向上",
           "B:高い", "2 - 高", "国内", "本社", "情報システム部",
           "ExcelによるT工数管理は月次集計に1人×3日を要している。専用ツール導入で自動化を実現。",
           "月次集計工数を3人日→0.5人日に削減。年間約20人日の削減効果。",
           "2027-04-01", 12_000_000, 15_000_000, "初期導入費8M、年間ライセンス4M（3年契約）",
           "HR部門との調整が必要。既存Excelとの移行計画を別途策定。",
           "screening", None, "セキュリティ審査完了。アーキテクチャ審査進行中。", None),

        _d("DMND1001011", "カスタマーサポート強化（AI活用）",
           "部門固有", "業務改善", "顧客サービス", "機能強化",
           "2026-09-01", "2027-06-30",
           u["木村 梅子"], "カスタマーサポート部", u["佐藤 事務局"], u["木村 梅子"], u["中村 五郎"],
           "Zendesk（APM-012）にAI自動応答機能を追加し、一次対応の自動化率を50%以上にする。",
           "顧客対応IT", "CX向上プログラム", "機能追加", "問い合わせ一次対応自動化率50%達成",
           "B:高い", "2 - 高", "国内", "本社", "カスタマーサポート部",
           "月間問い合わせ2000件のうち一次対応可能なFAQ系が60%。AI化で担当者工数を半減できる。",
           "担当者工数月120時間削減。顧客満足度スコア10%向上見込み。",
           "2027-07-01", 10_000_000, 12_000_000, "Zendesk AI機能ライセンス5M/年、設定費5M",
           "FAQ整備とナレッジベース構築が必要。",
           "screening", None, "セキュリティ審査完了。機能要件精査中。", None),

        _d("DMND1001012", "社内ポータル刷新（SharePointモダン化）",
           "全社共通", "インフラ刷新", "総務・コーポレート", "更改・移行",
           "2026-10-01", "2027-09-30",
           u["渡辺 四郎"], "総務部", u["佐藤 事務局"], u["渡辺 四郎"], u["山田 太郎"],
           "老朽化した社内ポータル（APM-014）をSharePoint Onlineのモダン機能でリニューアルし、情報発信力を強化する。",
           "コーポレートIT", "従業員体験向上プログラム", "更改", "情報発信の一元化と検索性向上",
           "A:確実", "3 - 中", "国内", "本社", "総務部",
           "現行ポータルは2015年構築。検索性が低く、重要通知が埋もれる課題がある。",
           "情報探索時間を月5時間→1時間に削減。全社通知の開封率20%向上。",
           "2027-10-01", 8_000_000, 10_000_000, "SharePoint設定費5M、デザイン・コンテンツ移行3M",
           "コンテンツ棚卸と情報オーナー整理が先行作業として必要。",
           "screening", None, "セキュリティ審査完了。コンテンツ整理計画を審査中。", None),

        # ── submitted (3件) ──
        _d("DMND1001013", "グローバル購買システム統合（第2フェーズ）",
           "グローバル展開", "インフラ刷新", "調達・購買", "更改・移行",
           "2027-04-01", "2029-03-31",
           u["伊藤 三郎"], "購買部", u["佐藤 事務局"], u["伊藤 三郎"], u["中村 五郎"],
           "DMND1001004（グローバルERP統合）の第2フェーズとして、アジア圏5拠点を順次統合する。",
           "グローバルERP", "グローバルSCM刷新プログラム", "更改", "アジア拠点の購買プロセス統合",
           "C:中程度", "1 - 最重要", "グローバル", "グループ全社", "購買部",
           "第1フェーズ完了後にアジア5拠点を追加統合。拠点ごとのカスタマイズが課題。",
           "アジア5拠点の運用コスト削減。現地調達効率化でリードタイム15%短縮。",
           "2029-04-01", 120_000_000, 150_000_000, "SAP追加ライセンス50M、移行費70M",
           "第1フェーズ完了を前提条件とする。各拠点責任者との合意が必要。",
           "submitted"),

        _d("DMND1001014", "製造設備IoT化・予防保全基盤構築",
           "部門固有", "戦略投資", "製造・品質", "新規導入",
           "2027-01-01", "2028-06-30",
           u["松本 十郎"], "製造部", u["佐藤 事務局"], u["松本 十郎"], u["中村 五郎"],
           "製造ラインの主要設備にIoTセンサーを設置し、予防保全プラットフォームを構築する。",
           "製造IT", "スマートファクトリー推進プログラム", "新規", "計画外停止ゼロ・予防保全体制の確立",
           "B:高い", "2 - 高", "国内", "本社", "製造部",
           "現在の事後保全では月平均2回の計画外停止が発生。IoT予防保全で年間損失2000万円を削減。",
           "計画外停止を年24回→4回以下に削減。設備稼働率を92%→97%に向上。",
           "2028-07-01", 45_000_000, 55_000_000, "IoTセンサー設置15M、プラットフォーム構築25M、年間保守5M",
           "既存設備管理システム（APM-010）との連携設計が必要。",
           "submitted"),

        _d("DMND1001015", "社内SNSプラットフォーム構築",
           "全社共通", "業務改善", "総務・コーポレート", "新規導入",
           "2026-12-01", "2027-09-30",
           u["林 竹子"], "広報部", u["佐藤 事務局"], u["渡辺 四郎"], u["山田 太郎"],
           "社内SNSを導入し、部門横断のナレッジ共有と社内コミュニケーション活性化を図る。",
           "コーポレートIT", "従業員体験向上プログラム", "新規", "部門横断ナレッジ共有の促進",
           "B:高い", "3 - 中", "国内", "本社", "広報部",
           "部門間のノウハウ共有がメールに依存しており、暗黙知の流失が課題。",
           "ナレッジ共有件数を月100件以上に。新入社員の立ち上がり期間を30%短縮。",
           "2027-10-01", 6_000_000, 8_000_000, "SaaSライセンス3M/年、導入・設定費3M",
           "社内ポータル（APM-014）との役割分担を明確化すること。",
           "submitted"),

        # ── draft (3件) ──
        _d("DMND1001016", "会議室予約システム導入",
           "全社共通", "業務改善", "総務・コーポレート", "新規導入",
           "2026-10-01", "2027-03-31",
           u["渡辺 四郎"], "総務部", u["佐藤 事務局"], u["渡辺 四郎"], u["山田 太郎"],
           "全社の会議室予約をシステム化し、二重予約ゼロと稼働率可視化を実現する。",
           "コーポレートIT", "オフィス環境改善プログラム", "新規", "会議室二重予約の根絶と稼働率向上",
           "A:確実", "3 - 中", "国内", "本社", "総務部",
           "年間約50件の二重予約トラブルが発生。Outlookカレンダーとの連携で解消可能。",
           "二重予約件数をゼロに。会議室稼働率の可視化で不要な会議室削減。",
           "2027-04-01", 4_000_000, 5_000_000, "SaaSライセンス2M/年、初期設定2M",
           "Microsoft 365連携が前提。IT部門との調整が必要。",
           "draft"),

        _d("DMND1001017", "研修管理システム導入（eラーニング統合）",
           "全社共通", "業務改善", "人事・労務", "新規導入",
           "2027-04-01", "2028-03-31",
           u["田中 花子"], "人事部", u["佐藤 事務局"], u["田中 花子"], u["山田 太郎"],
           "eラーニングと集合研修の管理を統合し、必須研修受講率100%を実現する基盤を整備する。",
           "コーポレートIT", "人材育成DXプログラム", "新規", "研修管理の一元化と受講率向上",
           "B:高い", "3 - 中", "国内", "本社", "人事部",
           "受講状況管理がExcelに依存。必須研修の受講漏れ追跡に月10時間かかる。",
           "必須研修受講率を85%→100%に。管理工数月10時間を0.5時間に削減。",
           "2028-04-01", 8_000_000, 10_000_000, "LMSライセンス4M/年、コンテンツ移行4M",
           "既存eラーニングコンテンツの移行計画策定が必要。",
           "draft"),

        _d("DMND1001018", "内部監査支援ツール導入",
           "全社共通", "コンプライアンス", "法務・契約", "新規導入",
           "2027-07-01", "2028-03-31",
           u["清水 松子"], "財務部", u["佐藤 事務局"], u["加藤 七子"], u["清水 松子"],
           "内部監査プロセスをデジタル化し、監査計画から指摘事項のフォローアップまでを一元管理する。",
           "コーポレートIT", "ガバナンス強化プログラム", "新規", "内部監査の効率化と証跡管理強化",
           "A:確実", "2 - 高", "国内", "本社", "財務部",
           "監査調書・指摘事項管理がExcelに依存し、追跡が困難。SOC2対応の観点からも電子化が必要。",
           "監査準備工数を月20時間削減。指摘事項フォローアップを100%追跡可能に。",
           "2028-04-01", 7_000_000, 9_000_000, "SaaSライセンス4M/年、導入費3M",
           "既存文書管理システム（APM-006）との連携を検討。",
           "draft"),

        # ── rejected (2件) ──
        _d("DMND1001019", "ブロックチェーン活用サプライチェーン基盤",
           "全社共通", "戦略投資", "調達・購買", "新規導入",
           "2025-10-01", "2027-03-31",
           u["中村 五郎"], "開発部", u["佐藤 事務局"], u["中村 五郎"], u["山田 太郎"],
           "ブロックチェーン技術を活用し、サプライチェーン全体のトレーサビリティ基盤を構築する。",
           "ITインフラ", "先進技術検証プログラム", "新規", "サプライチェーンの完全トレーサビリティ確立",
           "D:低い", "4 - 低", "グローバル", "グループ全社", "開発部",
           "ブロックチェーンによりサプライヤーから消費者までの物流を可視化する。",
           "偽造品混入ゼロ。サプライヤー監査コスト30%削減見込み。",
           "2027-04-01", 80_000_000, 100_000_000, "開発費60M、インフラ20M、コンソーシアム参加費用",
           "技術成熟度・費用対効果の観点から否決。2年後に再検討推奨。",
           "rejected", "費用対効果が現時点では不明確。技術成熟度が低く時期尚早と判断。",
           "技術審査では概念実証の段階。実用化に向けた課題が多数存在。", None),

        _d("DMND1001020", "AR/VR活用製造研修システム",
           "部門固有", "戦略投資", "人事・労務", "新規導入",
           "2025-07-01", "2026-09-30",
           u["田中 花子"], "人事部", u["佐藤 事務局"], u["松本 十郎"], u["中村 五郎"],
           "AR/VRを活用した製造現場向けのOJT代替研修システムを導入する。",
           "製造IT", "人材育成DXプログラム", "新規", "製造現場のOJT効率化と安全性向上",
           "D:低い", "3 - 中", "国内", "本社", "人事部",
           "新入社員OJTに製造現場での実機トレーニングが必要で危険。VR化で安全性を向上できる。",
           "OJT期間を6ヶ月→3ヶ月に短縮。設備損傷リスクゼロ。",
           "2026-10-01", 25_000_000, 30_000_000, "VRヘッドセット購入10M、コンテンツ開発15M",
           "費用対効果・技術成熟度の問題により否決。タブレット動画研修での代替を推奨。",
           "rejected", "VRコンテンツ開発の費用対効果が不十分。代替手段で目標達成可能と判断。",
           "コスト審査で費用対効果の問題を指摘。技術成熟度も課題。", None),
    ]

    for d in demands:
        cur.execute(
            """INSERT INTO demand
               (demand_id, title, it_class, category, domain, type,
                start_date, due_date,
                submitter_user_id, department_id, manager_user_id,
                system_owner_user_id, pm_user_id,
                description, portfolio, program, change_type, purpose,
                feasibility, priority, region, company, business_unit,
                business_case, expected_benefit,
                target_date, estimated_cost, requested_budget, cost_note, notes,
                stage, reject_reason, review_comment, approval_comment)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [d["demand_id"], d["title"], d["it_class"], d["category"], d["domain"], d["type"],
             d["start_date"], d["due_date"],
             d["submitter_user_id"], d["department_id"], d["manager_user_id"],
             d["system_owner_user_id"], d["pm_user_id"],
             d["description"], d["portfolio"], d["program"], d["change_type"], d["purpose"],
             d["feasibility"], d["priority"], d["region"], d["company"], d["business_unit"],
             d["business_case"], d["expected_benefit"],
             d["target_date"], d["estimated_cost"], d["requested_budget"], d["cost_note"], d["notes"],
             d["stage"], d["reject_reason"], d["review_comment"], d["approval_comment"]],
        )

    # ---------- デマンドタスク（55件） ----------
    # (task_id, demand_id, name, due_date, assignee_id, priority, state, comment, ai_gen, rationale)
    demand_tasks = [
        # DMND1001001 completed (4 tasks, all closed)
        ("DMNTSK4001001", "DMND1001001", "セキュリティ審査",   "2025-07-31", u["佐藤 事務局"], "2 - 高",    "closed", "Salesforceセキュリティ審査完了。問題なし。", 1, "SaaS利用基準適合確認"),
        ("DMNTSK4001002", "DMND1001001", "アーキテクチャ審査", "2025-08-31", u["山田 太郎"],  "2 - 高",    "closed", "既存CRMとのAPI連携設計承認。", 1, "既存システムとの連携設計確認"),
        ("DMNTSK4001003", "DMND1001001", "企画審査",           "2025-09-30", u["高橋 二郎"],  "3 - 中",    "closed", "ビジネスケース・費用対効果承認。", 1, "ビジネスケース確認"),
        ("DMNTSK4001004", "DMND1001001", "投資審査",           "2025-10-31", u["清水 松子"],  "1 - 最重要", "closed", "投資委員会承認取得。予算確定。", 1, "投資委員会への上程・承認取得"),
        # DMND1001002 completed (4 tasks, all closed)
        ("DMNTSK4002001", "DMND1001002", "セキュリティ審査",   "2024-12-31", u["佐藤 事務局"], "2 - 高",    "closed", "クラウドSaaSセキュリティ審査完了。", 1, "クラウドセキュリティ基準適合確認"),
        ("DMNTSK4002002", "DMND1001002", "アーキテクチャ審査", "2025-01-31", u["山田 太郎"],  "2 - 高",    "closed", "移行アーキテクチャ承認。データ移行計画確認。", 1, "移行設計妥当性確認"),
        ("DMNTSK4002003", "DMND1001002", "企画審査",           "2025-02-28", u["鈴木 一郎"],  "3 - 中",    "closed", "経費削減効果確認。ビジネスケース承認。", 1, "費用対効果の確認"),
        ("DMNTSK4002004", "DMND1001002", "投資審査",           "2025-03-31", u["清水 松子"],  "1 - 最重要", "closed", "ROI確認。投資委員会承認。", 1, "投資委員会承認"),
        # DMND1001003 completed (4 tasks, all closed)
        ("DMNTSK4003001", "DMND1001003", "セキュリティ審査",   "2024-06-30", u["佐藤 事務局"], "1 - 最重要", "closed", "TIME-Proセキュリティ審査完了。", 1, "勤怠データ保護要件確認"),
        ("DMNTSK4003002", "DMND1001003", "アーキテクチャ審査", "2024-07-31", u["山田 太郎"],  "2 - 高",    "closed", "クラウド移行設計承認。HR連携確認。", 1, "移行設計・HR連携確認"),
        ("DMNTSK4003003", "DMND1001003", "企画審査",           "2024-08-31", u["田中 花子"],  "3 - 中",    "closed", "テレワーク対応要件充足確認。", 1, "業務要件充足確認"),
        ("DMNTSK4003004", "DMND1001003", "投資審査",           "2024-09-30", u["清水 松子"],  "1 - 最重要", "closed", "3年間TCO比較で優位性確認。承認。", 1, "TCO比較・投資判断"),
        # DMND1001004 approved (3 tasks, all closed)
        ("DMNTSK4004001", "DMND1001004", "セキュリティ審査",   "2025-12-31", u["佐藤 事務局"], "1 - 最重要", "closed", "グローバルセキュリティ基準適合確認完了。", 1, "グローバルセキュリティ基準確認"),
        ("DMNTSK4004002", "DMND1001004", "アーキテクチャ審査", "2026-01-31", u["中村 五郎"],  "1 - 最重要", "closed", "SAP S/4HANA統合アーキテクチャ承認。", 1, "統合アーキテクチャ設計確認"),
        ("DMNTSK4004003", "DMND1001004", "投資審査",           "2026-02-28", u["清水 松子"],  "1 - 最重要", "closed", "200M投資、10年ROI試算承認。投資委員会通過。", 1, "大型投資の投資委員会承認"),
        # DMND1001005 approved (3 tasks, all closed)
        ("DMNTSK4005001", "DMND1001005", "セキュリティ審査",   "2025-10-31", u["佐藤 事務局"], "2 - 高",    "closed", "品質データの取り扱いセキュリティ確認完了。", 1, "製造データセキュリティ確認"),
        ("DMNTSK4005002", "DMND1001005", "アーキテクチャ審査", "2025-11-30", u["山田 太郎"],  "2 - 高",    "closed", "既存MESとの連携設計承認。", 1, "製造実行システム連携確認"),
        ("DMNTSK4005003", "DMND1001005", "投資審査",           "2025-12-31", u["清水 松子"],  "2 - 高",    "closed", "クレーム削減効果の費用対効果確認。承認。", 1, "品質改善ROI確認"),
        # DMND1001006 approved (3 tasks, all closed)
        ("DMNTSK4006001", "DMND1001006", "セキュリティ審査",   "2026-01-31", u["佐藤 事務局"], "2 - 高",    "closed", "電子署名のセキュリティ要件確認。法的有効性確認済み。", 1, "電子署名セキュリティ・法的要件確認"),
        ("DMNTSK4006002", "DMND1001006", "コンプライアンス審査", "2026-02-28", u["加藤 七子"], "1 - 最重要", "closed", "電子帳簿保存法・印紙税法対応確認完了。", 1, "電子契約の法令適合確認"),
        ("DMNTSK4006003", "DMND1001006", "投資審査",           "2026-03-31", u["清水 松子"],  "2 - 高",    "closed", "コスト削減効果確認。1年以内でROI回収。承認。", 1, "コスト削減ROI確認"),
        # DMND1001007 qualified (3 tasks: 2 closed, 1 inprogress)
        ("DMNTSK4007001", "DMND1001007", "セキュリティ審査",   "2026-11-30", u["佐藤 事務局"], "2 - 高",    "closed",     "LLMデータ取り扱いポリシー確認完了。", 1, "AIセキュリティポリシー確認"),
        ("DMNTSK4007002", "DMND1001007", "アーキテクチャ審査", "2026-12-31", u["中村 五郎"],  "2 - 高",    "closed",     "社内ナレッジ連携設計承認。RAG構成確認。", 1, "AI連携アーキテクチャ確認"),
        ("DMNTSK4007003", "DMND1001007", "投資審査",           "2027-01-31", u["清水 松子"],  "1 - 最重要", "inprogress", "工数削減効果の定量化を精査中。", 1, "AI投資対効果の定量評価"),
        # DMND1001008 qualified (3 tasks: 2 closed, 1 inprogress)
        ("DMNTSK4008001", "DMND1001008", "セキュリティ審査",   "2026-09-30", u["佐藤 事務局"], "1 - 最重要", "closed",     "S3・Redshiftのセキュリティ設計承認。", 1, "データ基盤セキュリティ設計確認"),
        ("DMNTSK4008002", "DMND1001008", "アーキテクチャ審査", "2026-10-31", u["中村 五郎"],  "1 - 最重要", "closed",     "Data Lake全体アーキテクチャ承認。", 1, "Data Lakeアーキテクチャ設計確認"),
        ("DMNTSK4008003", "DMND1001008", "投資審査",           "2026-11-30", u["清水 松子"],  "1 - 最重要", "inprogress", "年間運用コストの詳細試算を作成中。", 1, "クラウドコスト最適化計画確認"),
        # DMND1001009 qualified (3 tasks: 2 closed, 1 inprogress)
        ("DMNTSK4009001", "DMND1001009", "セキュリティ審査",   "2026-10-31", u["佐藤 事務局"], "2 - 高",    "closed",     "MA・CRM連携のセキュリティ設計承認。", 1, "SaaS間連携セキュリティ確認"),
        ("DMNTSK4009002", "DMND1001009", "アーキテクチャ審査", "2026-11-30", u["山田 太郎"],  "2 - 高",    "closed",     "HubSpot-Salesforce連携設計承認。", 1, "API連携設計確認"),
        ("DMNTSK4009003", "DMND1001009", "企画審査",           "2026-12-31", u["吉田 八郎"],  "3 - 中",    "inprogress", "コンバージョン改善効果の計測方法を検討中。", 1, "マーケティング効果測定計画確認"),
        # DMND1001010 screening (3 tasks: 1 closed, 1 inprogress, 1 open)
        ("DMNTSK4010001", "DMND1001010", "セキュリティ審査",   "2026-08-31", u["佐藤 事務局"], "2 - 高",    "closed",     "SaaSセキュリティ審査完了。問題なし。", 1, "工数管理SaaSセキュリティ確認"),
        ("DMNTSK4010002", "DMND1001010", "アーキテクチャ審査", "2026-09-30", u["山田 太郎"],  "2 - 高",    "inprogress", "既存勤怠システムとの連携設計を検討中。", 1, "既存システム連携設計確認"),
        ("DMNTSK4010003", "DMND1001010", "企画審査",           "2026-10-31", u["山田 太郎"],  "3 - 中",    "open",       None, 1, "ビジネスケース・費用対効果の確認"),
        # DMND1001011 screening (3 tasks: 1 closed, 1 inprogress, 1 open)
        ("DMNTSK4011001", "DMND1001011", "セキュリティ審査",   "2026-11-30", u["佐藤 事務局"], "2 - 高",    "closed",     "Zendesk AI機能セキュリティ審査完了。", 1, "AI機能のデータ取り扱い確認"),
        ("DMNTSK4011002", "DMND1001011", "アーキテクチャ審査", "2026-12-31", u["中村 五郎"],  "2 - 高",    "inprogress", "FAQデータ連携設計を検討中。", 1, "AI応答精度向上のための連携設計"),
        ("DMNTSK4011003", "DMND1001011", "企画審査",           "2027-01-31", u["木村 梅子"],  "3 - 中",    "open",       None, 1, "一次対応自動化率50%達成計画の確認"),
        # DMND1001012 screening (3 tasks: 1 closed, 1 inprogress, 1 open)
        ("DMNTSK4012001", "DMND1001012", "セキュリティ審査",   "2026-12-31", u["佐藤 事務局"], "2 - 高",    "closed",     "SharePoint Online セキュリティ設定審査完了。", 1, "M365セキュリティポリシー確認"),
        ("DMNTSK4012002", "DMND1001012", "アーキテクチャ審査", "2027-01-31", u["山田 太郎"],  "3 - 中",    "inprogress", "既存コンテンツの移行計画を策定中。", 1, "コンテンツ移行方針確認"),
        ("DMNTSK4012003", "DMND1001012", "企画審査",           "2027-02-28", u["渡辺 四郎"],  "3 - 中",    "open",       None, 1, "情報オーナー体制と運用ルール確認"),
        # DMND1001013 submitted (2 tasks, all open)
        ("DMNTSK4013001", "DMND1001013", "セキュリティ審査",   "2027-06-30", u["佐藤 事務局"], "1 - 最重要", "open", None, 1, "グローバルセキュリティ基準適合確認"),
        ("DMNTSK4013002", "DMND1001013", "アーキテクチャ審査", "2027-07-31", u["中村 五郎"],  "1 - 最重要", "open", None, 1, "第1フェーズとの整合性確認"),
        # DMND1001014 submitted (2 tasks, all open)
        ("DMNTSK4014001", "DMND1001014", "セキュリティ審査",   "2027-03-31", u["佐藤 事務局"], "2 - 高",    "open", None, 1, "IoTデバイスセキュリティ要件確認"),
        ("DMNTSK4014002", "DMND1001014", "アーキテクチャ審査", "2027-04-30", u["中村 五郎"],  "2 - 高",    "open", None, 1, "IoTプラットフォーム連携設計確認"),
        # DMND1001015 submitted (2 tasks, all open)
        ("DMNTSK4015001", "DMND1001015", "セキュリティ審査",   "2027-02-28", u["佐藤 事務局"], "2 - 高",    "open", None, 1, "社内SNSデータ管理ポリシー確認"),
        ("DMNTSK4015002", "DMND1001015", "アーキテクチャ審査", "2027-03-31", u["山田 太郎"],  "3 - 中",    "open", None, 1, "既存ポータルとの役割分担設計"),
        # DMND1001016 draft (2 tasks, all open)
        ("DMNTSK4016001", "DMND1001016", "セキュリティ審査",   "2026-12-31", u["佐藤 事務局"], "3 - 中", "open", None, 1, "M365カレンダー連携セキュリティ確認"),
        ("DMNTSK4016002", "DMND1001016", "アーキテクチャ審査", "2027-01-31", u["山田 太郎"],  "3 - 中", "open", None, 1, "Outlook連携設計確認"),
        # DMND1001017 draft (2 tasks, all open)
        ("DMNTSK4017001", "DMND1001017", "セキュリティ審査",   "2027-06-30", u["佐藤 事務局"], "3 - 中", "open", None, 1, "LMSデータセキュリティ確認"),
        ("DMNTSK4017002", "DMND1001017", "アーキテクチャ審査", "2027-07-31", u["山田 太郎"],  "3 - 中", "open", None, 1, "既存eラーニングシステム移行設計"),
        # DMND1001018 draft (2 tasks, all open)
        ("DMNTSK4018001", "DMND1001018", "セキュリティ審査",   "2027-09-30", u["佐藤 事務局"], "2 - 高", "open", None, 1, "監査データの機密性・完全性確認"),
        ("DMNTSK4018002", "DMND1001018", "コンプライアンス審査", "2027-10-31", u["加藤 七子"], "1 - 最重要", "open", None, 1, "内部監査規程との整合性確認"),
        # DMND1001019 rejected (2 tasks, all closed)
        ("DMNTSK4019001", "DMND1001019", "セキュリティ審査",   "2025-12-31", u["佐藤 事務局"], "3 - 中", "closed", "ブロックチェーンノードのセキュリティ要件を確認。懸念あり。", 1, "分散台帳セキュリティ確認"),
        ("DMNTSK4019002", "DMND1001019", "アーキテクチャ審査", "2026-01-31", u["中村 五郎"],  "3 - 中", "closed", "技術成熟度・既存インフラとの統合複雑性を指摘。否決推奨。", 1, "ブロックチェーン技術成熟度評価"),
        # DMND1001020 rejected (2 tasks, all closed)
        ("DMNTSK4020001", "DMND1001020", "セキュリティ審査",   "2025-09-30", u["佐藤 事務局"], "3 - 中", "closed", "VRヘッドセットの端末管理要件を確認。対応可能だが追加コスト発生。", 1, "VRデバイス管理セキュリティ確認"),
        ("DMNTSK4020002", "DMND1001020", "企画審査",           "2025-10-31", u["田中 花子"],  "3 - 中", "closed", "コンテンツ開発費が高額で費用対効果が不十分。代替案を推奨。", 1, "費用対効果・代替手段比較"),
    ]
    for (task_id, demand_id, name, due_date, assignee_id, priority, state, comment, ai_gen, rationale) in demand_tasks:
        cur.execute(
            """INSERT INTO demand_task
               (task_id, demand_id, name, due_date, assignee_user_id, priority, state, comment, ai_generated, rationale)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            [task_id, demand_id, name, due_date, assignee_id, priority, state, comment, ai_gen, rationale],
        )

    # ---------- demand_application（28件） ----------
    demand_apps = [
        ("DMND1001001", "APM-002", "CRM導入に伴う連携・移行対象"),
        ("DMND1001001", "APM-005", "旧CRM代替として廃止予定"),
        ("DMND1001002", "APM-004", "刷新対象：旧経費精算システム"),
        ("DMND1001003", "APM-013", "刷新対象：勤怠管理システム"),
        ("DMND1001004", "G-ERP",   "統合対象：グローバルERP基盤"),
        ("DMND1001005", "APM-011", "刷新対象：旧品質管理システム"),
        ("DMND1001006", "APM-008", "強化対象：法務契約管理システム"),
        ("DMND1001007", "APM-014", "チャットボット統合先：社内ポータル"),
        ("DMND1001007", "APM-012", "チャットボット連携：サポートチケット"),
        ("DMND1001008", "G-CLOUD", "Data Lake構築先：クラウド基盤"),
        ("DMND1001009", "APM-009", "強化対象：マーケティング自動化ツール"),
        ("DMND1001009", "APM-002", "連携強化対象：営業支援CRM"),
        ("DMND1001010", "APM-001", "連携対象：人事・給与システム"),
        ("DMND1001010", "APM-013", "連携対象：勤怠管理システム"),
        ("DMND1001011", "APM-012", "強化対象：カスタマーサポートチケット管理"),
        ("DMND1001012", "APM-014", "刷新対象：社内ポータル"),
        ("DMND1001013", "APM-003", "統合対象：在庫・購買管理システム"),
        ("DMND1001013", "G-ERP",   "統合先：グローバルERP基盤"),
        ("DMND1001014", "APM-010", "連携対象：設備管理システム"),
        ("DMND1001015", "APM-014", "連携先：社内ポータル（SNS統合候補）"),
        ("DMND1001016", "APM-014", "統合候補：社内ポータルへの機能追加"),
        ("DMND1001016", "APM-006", "代替候補：文書管理システムとの統合"),
        ("DMND1001017", "APM-001", "連携対象：人事システム（受講履歴連携）"),
        ("DMND1001018", "APM-006", "連携候補：文書管理システム"),
        ("DMND1001019", "G-CLOUD", "基盤活用予定：クラウド基盤"),
        ("DMND1001020", "APM-001", "連携対象：人事システム（研修記録）"),
        ("DMND1001020", "APM-013", "連携対象：勤怠管理（研修時間計上）"),
        ("DMND1001020", "APM-014", "配信先候補：社内ポータル"),
    ]
    for (did, aid, note) in demand_apps:
        cur.execute(
            "INSERT INTO demand_application (demand_id, application_id, relation_note) VALUES (?,?,?)",
            [did, aid, note],
        )

    # ---------- cost_plan（55件） ----------
    cost_plans = [
        # DMND1001001 completed (4件, actual_cost filled)
        ("DMND1001001", 2025, "Q2", "開発費",       3_000_000, 1, 3_000_000, 2_800_000, "Salesforceカスタマイズ開発"),
        ("DMND1001001", 2025, "Q3", "ライセンス費", 5_000_000, 1, 5_000_000, 5_000_000, "Salesforceライセンス初年度"),
        ("DMND1001001", 2025, "Q4", "導入費",       1_500_000, 1, 1_500_000, 1_600_000, "データ移行・トレーニング費"),
        ("DMND1001001", 2026, "Q1", "運用費",       1_250_000, 1, 1_250_000, 1_250_000, "ライセンス更新（Q1分）"),
        # DMND1001002 completed (4件, actual_cost filled)
        ("DMND1001002", 2024, "Q4", "開発費",       3_000_000, 1, 3_000_000, 2_900_000, "移行設計・データ移行"),
        ("DMND1001002", 2025, "Q1", "ライセンス費", 3_000_000, 1, 3_000_000, 3_000_000, "SaaSライセンス初年度"),
        ("DMND1001002", 2025, "Q2", "導入費",       1_000_000, 1, 1_000_000, 1_100_000, "トレーニング・マニュアル作成"),
        ("DMND1001002", 2025, "Q3", "運用費",         750_000, 1,   750_000,   750_000, "ライセンス更新（Q3分）"),
        # DMND1001003 completed (4件, actual_cost filled)
        ("DMND1001003", 2024, "Q2", "開発費",       3_000_000, 1, 3_000_000, 3_200_000, "TIME-Pro移行・設定"),
        ("DMND1001003", 2024, "Q3", "ライセンス費", 2_000_000, 1, 2_000_000, 2_000_000, "TIME-Proライセンス初年度"),
        ("DMND1001003", 2024, "Q4", "導入費",         800_000, 1,   800_000,   750_000, "全社トレーニング費"),
        ("DMND1001003", 2025, "Q1", "運用費",         500_000, 1,   500_000,   500_000, "ライセンス更新（Q1分）"),
        # DMND1001004 approved (3件)
        ("DMND1001004", 2026, "Q3", "開発費",      50_000_000, 1, 50_000_000, 0, "SAP S/4HANA設計・構築フェーズ1"),
        ("DMND1001004", 2027, "Q1", "開発費",      80_000_000, 1, 80_000_000, 0, "移行・テスト・展開"),
        ("DMND1001004", 2027, "Q3", "ライセンス費", 50_000_000, 1, 50_000_000, 0, "SAP年間ライセンス"),
        # DMND1001005 approved (3件)
        ("DMND1001005", 2026, "Q2", "開発費",       7_000_000, 1,  7_000_000, 0, "品質管理SaaS導入・設定費"),
        ("DMND1001005", 2026, "Q3", "ライセンス費", 8_000_000, 1,  8_000_000, 0, "年間ライセンス費"),
        ("DMND1001005", 2026, "Q4", "運用費",       1_500_000, 1,  1_500_000, 0, "保守・サポート費"),
        # DMND1001006 approved (3件)
        ("DMND1001006", 2026, "Q2", "開発費",       3_000_000, 1,  3_000_000, 0, "DocuSign電子契約機能設定費"),
        ("DMND1001006", 2026, "Q3", "ライセンス費", 2_000_000, 1,  2_000_000, 0, "追加ライセンス費"),
        ("DMND1001006", 2026, "Q4", "その他",         500_000, 1,    500_000, 0, "取引先対応・周知費用"),
        # DMND1001007 qualified (3件)
        ("DMND1001007", 2027, "Q1", "開発費",       8_000_000, 1,  8_000_000, 0, "チャットボット開発・FAQデータ整備"),
        ("DMND1001007", 2027, "Q2", "ライセンス費", 4_000_000, 1,  4_000_000, 0, "LLMサービス利用料"),
        ("DMND1001007", 2027, "Q3", "運用費",       1_500_000, 1,  1_500_000, 0, "年間保守費"),
        # DMND1001008 qualified (3件)
        ("DMND1001008", 2027, "Q1", "開発費",      20_000_000, 1, 20_000_000, 0, "Data Lake構築費（AWS）"),
        ("DMND1001008", 2027, "Q2", "インフラ費",  10_000_000, 1, 10_000_000, 0, "AWSインフラ年間費用"),
        ("DMND1001008", 2027, "Q3", "運用費",       5_000_000, 1,  5_000_000, 0, "データエンジニアリング保守費"),
        # DMND1001009 qualified (3件)
        ("DMND1001009", 2026, "Q4", "開発費",       5_000_000, 1,  5_000_000, 0, "HubSpot-Salesforce連携開発費"),
        ("DMND1001009", 2027, "Q1", "ライセンス費", 3_000_000, 1,  3_000_000, 0, "HubSpot追加ライセンス"),
        ("DMND1001009", 2027, "Q2", "その他",       1_000_000, 1,  1_000_000, 0, "データクレンジング・移行費"),
        # DMND1001010 screening (3件)
        ("DMND1001010", 2026, "Q4", "開発費",       8_000_000, 1,  8_000_000, 0, "工数管理ツール導入・設定費"),
        ("DMND1001010", 2027, "Q1", "ライセンス費", 4_000_000, 1,  4_000_000, 0, "年間ライセンス費"),
        ("DMND1001010", 2027, "Q2", "その他",         500_000, 1,    500_000, 0, "研修・マニュアル作成"),
        # DMND1001011 screening (3件)
        ("DMND1001011", 2027, "Q1", "開発費",       5_000_000, 1,  5_000_000, 0, "Zendesk AI設定・FAQデータ整備"),
        ("DMND1001011", 2027, "Q2", "ライセンス費", 5_000_000, 1,  5_000_000, 0, "AI機能年間ライセンス"),
        ("DMND1001011", 2027, "Q3", "その他",         500_000, 1,    500_000, 0, "効果測定・運用支援費"),
        # DMND1001012 screening (3件)
        ("DMND1001012", 2027, "Q2", "開発費",       5_000_000, 1,  5_000_000, 0, "SharePoint モダン化設計・構築"),
        ("DMND1001012", 2027, "Q3", "導入費",       3_000_000, 1,  3_000_000, 0, "コンテンツ移行・デザイン費"),
        ("DMND1001012", 2027, "Q4", "その他",         500_000, 1,    500_000, 0, "トレーニング・運用サポート費"),
        # DMND1001013 submitted (2件)
        ("DMND1001013", 2027, "Q3", "開発費",      70_000_000, 1, 70_000_000, 0, "第2フェーズ移行設計・構築"),
        ("DMND1001013", 2028, "Q1", "ライセンス費", 50_000_000, 1, 50_000_000, 0, "SAP追加ライセンス"),
        # DMND1001014 submitted (2件)
        ("DMND1001014", 2027, "Q2", "開発費",      25_000_000, 1, 25_000_000, 0, "IoTプラットフォーム構築費"),
        ("DMND1001014", 2027, "Q3", "インフラ費",  15_000_000, 1, 15_000_000, 0, "センサー設置・インフラ費"),
        # DMND1001015 submitted (2件)
        ("DMND1001015", 2027, "Q2", "開発費",       3_000_000, 1,  3_000_000, 0, "社内SNS導入・設定費"),
        ("DMND1001015", 2027, "Q3", "ライセンス費", 3_000_000, 1,  3_000_000, 0, "年間ライセンス費"),
        # DMND1001016 draft (2件)
        ("DMND1001016", 2027, "Q1", "開発費",       2_000_000, 1,  2_000_000, 0, "会議室予約システム初期設定費"),
        ("DMND1001016", 2027, "Q2", "ライセンス費", 2_000_000, 1,  2_000_000, 0, "年間ライセンス費"),
        # DMND1001017 draft (2件)
        ("DMND1001017", 2027, "Q4", "開発費",       4_000_000, 1,  4_000_000, 0, "LMS導入・コンテンツ移行費"),
        ("DMND1001017", 2028, "Q1", "ライセンス費", 4_000_000, 1,  4_000_000, 0, "年間ライセンス費"),
        # DMND1001018 draft (2件)
        ("DMND1001018", 2027, "Q4", "開発費",       3_000_000, 1,  3_000_000, 0, "内部監査ツール導入費"),
        ("DMND1001018", 2028, "Q1", "ライセンス費", 4_000_000, 1,  4_000_000, 0, "年間ライセンス費"),
        # DMND1001019 rejected (2件)
        ("DMND1001019", 2026, "Q1", "開発費",      60_000_000, 1, 60_000_000, 0, "ブロックチェーン基盤構築費（否決）"),
        ("DMND1001019", 2026, "Q2", "インフラ費",  20_000_000, 1, 20_000_000, 0, "ノードインフラ費（否決）"),
        # DMND1001020 rejected (2件)
        ("DMND1001020", 2025, "Q4", "開発費",      15_000_000, 1, 15_000_000, 0, "VRコンテンツ開発費（否決）"),
        ("DMND1001020", 2026, "Q1", "その他",      10_000_000, 1, 10_000_000, 0, "VRヘッドセット購入費（否決）"),
    ]
    for (did, fy, fp, ct, uc, qty, pc, ac, note) in cost_plans:
        cur.execute(
            """INSERT INTO cost_plan
               (demand_id, fiscal_year, fiscal_period, cost_type, unit_cost, quantity, planned_cost, actual_cost, note)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            [did, fy, fp, ct, uc, qty, pc, ac, note],
        )

    # ---------- プロジェクト（5件） ----------
    projects = [
        ("PROJ00001", "DMND1001001", "営業支援CRM導入（国内営業部門）",      "completed", "2025-11-01"),
        ("PROJ00002", "DMND1001002", "経費精算システム刷新",                 "completed", "2025-04-01"),
        ("PROJ00003", "DMND1001003", "勤怠管理システム刷新（クラウド移行）", "completed", "2024-10-01"),
        ("PROJ00004", "DMND1001004", "グローバルERP統合推進",                "active",    "2026-05-01"),
        ("PROJ00005", "DMND1001005", "品質管理システム刷新",                 "active",    "2026-03-01"),
    ]
    for (pid, did, title, status, created) in projects:
        cur.execute(
            """INSERT INTO project (project_id, demand_id, title, status, created_date)
               VALUES (?,?,?,?,?)""",
            [pid, did, title, status, created],
        )
    conn.commit()
    conn.close()
    print("✓ シードデータを投入しました")
    print(f"  部署: {len(departments)}件, ユーザー: {len(users)}件")
    print(f"  アプリケーション: {len(apps)}件 (インフラ含む), 環境: {len(envs)}件")
    print(f"  CI: {len(ci_data)}件, 依存関係: {len(deps)}件, 申請: {len(requests)}件")
    print(f"  デマンド: {len(demands)}件, タスク: {len(demand_tasks)}件, 関連アプリ: {len(demand_apps)}件")
    print(f"  コスト計画: {len(cost_plans)}件, プロジェクト: {len(projects)}件")


if __name__ == "__main__":
    seed()
