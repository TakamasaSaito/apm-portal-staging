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
  related_application_id TEXT,
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
    """)

    # 既存データクリア（FK OFF なので順序自由）
    for table in [
        "demand_task", "project", "demand",
        "apm_request", "configuration_item", "environment",
        "application_dependency", "application", "user", "department",
    ]:
        cur.execute(f"DELETE FROM {table}")

    # ---------- 部署 ----------
    departments = ["人事部", "営業本部", "購買部", "経理部", "総務部", "情報システム部"]
    dept_ids: dict = {}
    for d in departments:
        cur.execute("INSERT INTO department (department_name) VALUES (?)", [d])
        dept_ids[d] = cur.lastrowid

    # ---------- ユーザー ----------
    users = [
        ("申請者ユーザー", "情報システム部", "applicant", "user",  _hash("user")),
        ("事務局ユーザー", "情報システム部", "admin",     "admin", _hash("admin")),
        ("田中 花子",     "購買部",         "applicant", None, None),
        ("山田 太郎",     "人事部",         "applicant", None, None),
        ("鈴木 一郎",     "人事部",         "applicant", None, None),
        ("高橋 二郎",     "営業本部",       "applicant", None, None),
        ("佐藤 事務局",   "情報システム部", "admin",     None, None),
    ]
    user_ids: dict = {}
    for name, dept, role, login_id, password_hash in users:
        cur.execute(
            "INSERT INTO user (user_name, department_id, role, login_id, password_hash) VALUES (?, ?, ?, ?, ?)",
            [name, dept_ids[dept], role, login_id, password_hash],
        )
        user_ids[name] = cur.lastrowid

    # ---------- アプリケーション ----------
    # 各フィールド: id, name, dept, status, vendor,
    #   biz_owner, sys_owner, ops_mgr, dev_mgr,
    #   start_plan, start_actual, end_plan, end_actual, app_category,
    #   portfolio_area, migration_target_id, annual_cost, is_infra
    apps = [
        # ── グローバル基盤（先に投入：他が参照する migration_target）──
        ("G-CLOUD", "グローバルクラウド基盤(AWS)",    "情報システム部", "running",
         "Amazon Web Services",
         "CTO", "クラウド課長", "クラウド主任", "クラウド主任",
         "2022-04-01", "2022-04-01", None, None,
         "Cloud Platform（クラウド基盤）",
         4, None, 6200, 1),

        ("G-SSO",   "グローバル認証基盤(SSO)",        "情報システム部", "running",
         "Microsoft Azure AD",
         "CTO", "セキュリティ課長", "セキュリティ主任", "セキュリティ主任",
         "2023-01-01", "2023-01-01", None, None,
         "Security（セキュリティ管理）",
         4, None, 3800, 1),

        ("G-HRM",   "グローバルHRM",                  "人事部",         "dev",
         "Workday",
         "人事部長", "人事システム課長", "未定", "HRMプロジェクトPM",
         "2026-10-01", None, None, None,
         "HRM（人事・労務・給与）",
         4, None, 4800, 0),

        ("G-ERP",   "グローバルERP",                  "経理部",         "running",
         "SAP",
         "CFO", "ERPシステム課長", "ERP運用主任", "ERPプロジェクトPM",
         "2023-07-01", "2023-07-01", None, None,
         "ERP（基幹業務）",
         4, None, 5500, 0),

        # ── 国内インフラ（G-CLOUD/G-SSO を参照）──
        ("INF-DC1",  "国内データセンター基盤",         "情報システム部", "running",
         "NTTデータ",
         "情報システム部長", "インフラ課長", "インフラ主任", "インフラ主任",
         "2015-04-01", "2015-04-01", "2027-03-31", None,
         "Infrastructure（インフラ・サーバー・クラウド）",
         2, "G-CLOUD", 1200, 1),

        ("INF-AUTH", "国内認証基盤",                   "情報システム部", "running",
         "株式会社ID管理",
         "情報システム部長", "セキュリティ課長", "セキュリティ主任", "セキュリティ主任",
         "2016-06-01", "2016-06-01", "2026-09-30", None,
         "Security（セキュリティ管理）",
         2, "G-SSO", 900, 1),

        # ── 業務アプリ APM-001 〜 APM-006 ──
        ("APM-001", "人事管理システム",                "人事部",         "running",
         "株式会社HR-Tech",
         "田中 部長", "山田 課長", "鈴木 主任", "佐藤 主任",
         "2021-04-01", "2021-04-01", "2028-03-31", None,
         "HRM（人事・労務・給与）",
         2, None, 850, 0),

        ("APM-002", "営業支援システム（SFA）",         "営業本部",       "running",
         "Salesforce Japan",
         "高橋 部長", "伊藤 課長", "渡辺 主任", "中村 主任",
         "2020-10-01", "2020-10-15", "2027-09-30", None,
         "CRM（顧客管理・営業支援）",
         2, None, 620, 0),

        ("APM-003", "在庫管理システム",                "購買部",         "running",
         "株式会社SCM-Pro",
         "小林 部長", "加藤 課長", "吉田 主任", "山本 主任",
         "2019-07-01", "2019-07-01", "2027-06-30", None,
         "SCM（サプライチェーン・購買・在庫）",
         2, None, 480, 0),

        ("APM-004", "経費精算システム",                "経理部",         "running",
         "株式会社FinTech",
         "松本 部長", "井上 課長", "木村 主任", "林 主任",
         "2022-01-01", "2022-02-01", "2029-03-31", None,
         "Finance（経理・財務・予算）",
         2, None, 520, 0),

        ("APM-005", "顧客管理システム（CRM）",         "営業本部",       "dev",
         "Salesforce Japan",
         "高橋 部長", "石川 課長", "前田 主任", "前田 主任",
         "2025-10-01", None, None, None,
         "CRM（顧客管理・営業支援）",
         3, None, 720, 0),

        ("APM-006", "文書管理システム",                "総務部",         "plan",
         "未定",
         "清水 部長", "未定", "未定", "未定",
         "2026-04-01", None, None, None,
         "Document Management（文書・コンテンツ管理）",
         3, None, 380, 0),

        # ── APM-007（G-HRM を参照）──
        ("APM-007", "旧給与計算システム",              "人事部",         "retire",
         "株式会社レガシーSI",
         "田中 部長", "退任", "退任", "退任",
         "2010-04-01", "2010-04-01", "2026-03-31", None,
         "HRM（人事・労務・給与）",
         1, "G-HRM", 450, 0),

        # ── APM-008 〜 APM-013 ──
        ("APM-008", "購買管理システム",                "購買部",         "running",
         "株式会社SCM-Pro",
         "小林 部長", "加藤 課長", "吉田 主任", "山本 主任",
         "2018-04-01", "2018-04-01", "2028-03-31", None,
         "SCM（サプライチェーン・購買・在庫）",
         3, None, 300, 0),

        ("APM-009", "法務契約管理システム",            "総務部",         "running",
         "DocuSign Japan",
         "清水 部長", "藤田 課長", "岡田 主任", "中島 主任",
         "2020-07-01", "2020-07-15", "2026-11-30", None,
         "Legal / Compliance（法務・コンプライアンス）",
         3, None, 250, 0),

        ("APM-010", "マーケティング自動化ツール",      "営業本部",       "running",
         "HubSpot Japan",
         "高橋 部長", "石川 課長", "前田 主任", "村田 主任",
         "2021-10-01", "2021-11-01", "2028-09-30", None,
         "Marketing（マーケティング）",
         3, None, 350, 0),

        ("APM-011", "ITサービス管理システム（ITSM）",  "情報システム部", "running",
         "ServiceNow Japan",
         "佐藤 部長", "田中 課長", "鈴木 主任", "高橋 主任",
         "2019-04-01", "2019-04-01", "2029-03-31", None,
         "ITSM / ITOM（ITサービス・運用管理）",
         3, None, 420, 0),

        ("APM-012", "ネットワーク管理システム",        "情報システム部", "running",
         "NETSCOUT",
         "佐藤 部長", "山田 課長", "井上 主任", "木村 主任",
         "2017-10-01", "2017-10-01", "2027-03-31", None,
         "Network（ネットワーク）",
         2, None, 280, 1),

        ("APM-013", "セキュリティ管理プラットフォーム", "情報システム部", "running",
         "CrowdStrike",
         "佐藤 部長", "渡辺 課長", "伊藤 主任", "中村 主任",
         "2022-04-01", "2022-05-01", "2030-03-31", None,
         "Security（セキュリティ管理）",
         3, None, 560, 0),

        # ── APM-014（G-CLOUD を参照）──
        ("APM-014", "サーバー監視システム",            "情報システム部", "running",
         "Datadog",
         "佐藤 部長", "加藤 課長", "吉田 主任", "松本 主任",
         "2016-07-01", "2016-07-01", "2026-12-31", None,
         "Monitoring（監視・ログ管理）",
         1, "G-CLOUD", 180, 1),

        # ── APM-015 〜 APM-018 ──
        ("APM-015", "クラウド基盤管理ポータル",        "情報システム部", "running",
         "Amazon Web Services",
         "佐藤 部長", "林 課長", "清水 主任", "山口 主任",
         "2020-01-01", "2020-02-01", "2030-12-31", None,
         "Cloud Platform（クラウド基盤）",
         4, None, 320, 1),

        ("APM-016", "BIレポーティングツール",          "経理部",         "running",
         "Tableau Software",
         "松本 部長", "井上 課長", "木村 主任", "林 主任",
         "2021-07-01", "2021-07-01", "2028-06-30", None,
         "BI / Analytics（分析・レポート）",
         3, None, 290, 0),

        ("APM-017", "データ連携基盤（ETL）",           "情報システム部", "running",
         "株式会社インフォマティカ",
         "佐藤 部長", "田中 課長", "鈴木 主任", "高橋 主任",
         "2019-10-01", "2019-10-01", "2027-09-30", None,
         "Data Integration（データ連携・ETL）",
         3, None, 460, 0),

        ("APM-018", "グループウェア",                  "総務部",         "running",
         "Google Workspace",
         "清水 部長", "藤田 課長", "岡田 主任", "中島 主任",
         "2015-04-01", "2015-04-01", "2027-03-31", None,
         "Collaboration（グループウェア・社内コミュニケーション）",
         2, None, 380, 0),

        # ── APM-019（G-ERP を参照）──
        ("APM-019", "基幹ERPシステム",                 "経理部",         "running",
         "旧ベンダー",
         "松本 部長", "佐々木 課長", "大野 主任", "石田 主任",
         "2014-04-01", "2014-04-01", "2029-03-31", None,
         "ERP（基幹業務）",
         2, "G-ERP", 1200, 0),

        # ── APM-020 〜 APM-027 ──
        ("APM-020", "採用管理システム",                "人事部",         "running",
         "SmartHR",
         "田中 部長", "山田 課長", "鈴木 主任", "中川 主任",
         "2023-04-01", "2023-04-01", "2030-03-31", None,
         "HRM（人事・労務・給与）",
         3, None, 220, 0),

        ("APM-021", "旧在庫管理システム",              "購買部",         "retire",
         "株式会社レガシーSI",
         "小林 部長", "退任", "退任", "退任",
         "2008-04-01", "2008-04-01", "2019-06-30", "2019-06-30",
         "SCM（サプライチェーン・購買・在庫）",
         1, None, 120, 0),

        ("APM-022", "旧グループウェア（Notes）",       "総務部",         "retire",
         "IBM",
         "清水 部長", "退任", "退任", "退任",
         "2005-04-01", "2005-04-01", "2015-03-31", "2015-03-31",
         "Collaboration（グループウェア・社内コミュニケーション）",
         1, None, 80, 0),

        ("APM-023", "ERP刷新プロジェクト",             "経理部",         "dev",
         "SAP Japan",
         "松本 部長", "佐々木 課長", "未定", "大野 主任",
         "2026-10-01", None, None, None,
         "ERP（基幹業務）",
         2, None, 800, 0),

        ("APM-024", "データ分析基盤刷新",              "情報システム部", "plan",
         "Databricks",
         "佐藤 部長", "未定", "未定", "未定",
         "2027-04-01", None, None, None,
         "BI / Analytics（分析・レポート）",
         2, None, 450, 0),

        ("APM-025", "予算管理システム",                "経理部",         "order",
         "株式会社Freee",
         "松本 部長", "井上 課長", "未定", "石田 主任",
         "2025-12-01", None, None, None,
         "Finance（経理・財務・予算）",
         3, None, 340, 0),

        ("APM-026", "DBaaSプラットフォーム",           "情報システム部", "running",
         "Amazon Web Services",
         "佐藤 部長", "渡辺 課長", "伊藤 主任", "村山 主任",
         "2021-04-01", "2021-04-01", "2031-03-31", None,
         "Database（データベース）",
         4, None, 680, 1),

        ("APM-027", "コンプライアンス管理ツール",      "総務部",         "running",
         "MetricStream",
         "清水 部長", "藤田 課長", "岡田 主任", "西村 主任",
         "2023-07-01", "2023-07-01", "2030-06-30", None,
         "Legal / Compliance（法務・コンプライアンス）",
         3, None, 260, 0),
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

    # ---------- 依存関係 ----------
    deps = [
        ("APM-001", "INF-DC1",  "infra", "オンプレサーバー上で稼働"),
        ("APM-001", "INF-AUTH", "auth",  "社内認証基盤でSSO連携"),
        ("APM-002", "INF-AUTH", "auth",  "社内認証基盤でSSO連携"),
        ("APM-002", "G-SSO",    "auth",  "グローバルSSO連携（一部）"),
        ("APM-003", "INF-DC1",  "infra", "オンプレサーバー上で稼働"),
        ("APM-003", "INF-AUTH", "auth",  "社内認証基盤でSSO連携"),
        ("APM-004", "INF-AUTH", "auth",  "社内認証基盤でSSO連携"),
        ("APM-004", "G-CLOUD",  "infra", "AWS上でホスティング"),
        ("APM-005", "G-SSO",    "auth",  "グローバルSSO連携"),
        ("APM-005", "G-CLOUD",  "infra", "AWS上で開発中"),
        ("APM-006", "G-SSO",    "auth",  "グローバルSSO連携予定"),
        ("APM-006", "G-CLOUD",  "infra", "AWS上で構築予定"),
        ("APM-007", "INF-DC1",  "infra", "オンプレサーバー上で稼働（廃止予定）"),
        ("APM-007", "INF-AUTH", "auth",  "社内認証基盤（廃止予定）"),
        ("INF-AUTH","G-SSO",    "auth",  "グローバルSSO移行中"),
        ("INF-DC1", "G-CLOUD",  "infra", "AWSへ移行中"),
        ("G-ERP",   "G-SSO",    "auth",  "グローバルSSO連携"),
        ("G-ERP",   "G-CLOUD",  "infra", "AWS上で稼働"),
        ("G-HRM",   "G-SSO",    "auth",  "グローバルSSO連携予定"),
        ("G-HRM",   "G-CLOUD",  "infra", "AWS上で開発中"),
    ]
    for app_id, dep_id, dep_type, note in deps:
        cur.execute(
            """INSERT INTO application_dependency
                   (app_id, depends_on_app_id, dependency_type, note)
               VALUES (?, ?, ?, ?)""",
            [app_id, dep_id, dep_type, note],
        )

    # ---------- 環境 ----------
    envs = [
        ("APM-001", "本番環境",       "東京DC",               "10.1.1.10",    "hr-prod.corp.local",      "RHEL 8.6",            "Tomcat 10/Java17",     "8vCPU/32GB",  "1TB SSD"),
        ("APM-001", "ステージング環境", "東京DC",               "10.1.2.10",    "hr-stg.corp.local",       "RHEL 8.6",            "Tomcat 10/Java17",     "4vCPU/16GB",  "500GB SSD"),
        ("APM-001", "開発環境",       "AWS ap-northeast-1",   "172.31.0.10",  "hr-dev.corp.local",       "RHEL 8.6",            "Tomcat 10/Java17",     "2vCPU/8GB",   "200GB SSD"),
        ("APM-002", "本番環境",       "Azure Japan East",     "40.79.180.x",  "sfa-prod.corp.local",     "Windows Server 2022", ".NET 7/IIS",           "8vCPU/16GB",  "500GB SSD"),
        ("APM-002", "テスト環境",     "Azure Japan East",     "40.79.181.x",  "sfa-test.corp.local",     "Windows Server 2022", ".NET 7/IIS",           "4vCPU/8GB",   "200GB SSD"),
        ("APM-003", "本番環境",       "大阪DC",               "192.168.10.20","inv-prod.corp.local",     "CentOS 7.9",          "Apache/PHP 8.1",       "4vCPU/16GB",  "2TB HDD"),
        ("APM-003", "ステージング環境", "大阪DC",               "192.168.11.20","inv-stg.corp.local",      "CentOS 7.9",          "Apache/PHP 8.1",       "2vCPU/8GB",   "500GB HDD"),
        ("APM-003", "開発環境",       "大阪DC",               "192.168.12.20","inv-dev.corp.local",      "CentOS 7.9",          "Apache/PHP 8.1",       "2vCPU/4GB",   "200GB HDD"),
        ("APM-004", "本番環境",       "AWS ap-northeast-1",   "52.194.x.x",  "expense-prod.corp.local", "Amazon Linux 2",      "Node.js 18/PM2",       "4vCPU/8GB",   "200GB SSD"),
        ("APM-004", "開発環境",       "AWS ap-northeast-1",   "52.195.x.x",  "expense-dev.corp.local",  "Amazon Linux 2",      "Node.js 18/PM2",       "2vCPU/4GB",   "100GB SSD"),
        ("APM-005", "開発環境",       "AWS ap-northeast-1",   "（未割当）",   "crm-dev.corp.local",      "Amazon Linux 2",      "Python 3.11/FastAPI",  "2vCPU/4GB",   "100GB SSD"),
    ]
    env_ids: dict = {}
    for row in envs:
        cur.execute(
            """INSERT INTO environment
                   (application_id, env_type, location, ip, host, os, middleware, cpu_mem, storage)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            list(row),
        )
        env_ids[(row[0], row[1])] = cur.lastrowid

    # ---------- 構成情報（CI） ----------
    def eid(app_id, env_type):
        return env_ids.get((app_id, env_type))

    ci_data = [
        (eid("APM-001","本番環境"),       "hr-web-prod-01",   "Server",  "hr-web-prod-01.corp.local",   "10.1.1.11",    "10.1.1.200", "RHEL 8.6","8.6.0","Intel Xeon Gold 6248R 3.0GHz 20C","32GB DDR4 ECC","500GB SSD","Dell","PowerEdge R650","active","APサーバー兼任"),
        (eid("APM-001","本番環境"),       "hr-db-prod-01",    "DB",      "hr-db-prod-01.corp.local",    "10.1.1.12",    "10.1.1.201", "RHEL 8.6","8.6.0","Intel Xeon Gold 6248R 3.0GHz 20C","64GB DDR4 ECC","2TB SSD RAID1","Dell","PowerEdge R650","active","PostgreSQL 15"),
        (eid("APM-001","本番環境"),       "hr-lb-prod-01",    "Network", "hr-lb-prod-01.corp.local",    "10.1.1.10",    "10.1.1.202", None,None,None,None,None,"F5","BIG-IP i2600","active","ロードバランサー VIP 10.1.1.10"),
        (eid("APM-001","ステージング環境"),"hr-web-stg-01",   "Server",  "hr-web-stg-01.corp.local",    "10.1.2.11",    "10.1.2.200", "RHEL 8.6","8.6.0","Intel Xeon Silver 4214R 2.4GHz 12C","16GB DDR4","300GB SSD","Dell","PowerEdge R550","active","Web/APサーバー"),
        (eid("APM-001","ステージング環境"),"hr-db-stg-01",    "DB",      "hr-db-stg-01.corp.local",     "10.1.2.12",    "10.1.2.201", "RHEL 8.6","8.6.0","Intel Xeon Silver 4214R 2.4GHz 12C","32GB DDR4","1TB SSD","Dell","PowerEdge R550","active","PostgreSQL 15"),
        (eid("APM-002","本番環境"),       "sfa-ap-prod-01",   "Server",  "sfa-ap-prod-01.corp.local",   "40.79.180.11", None,         "Windows Server 2022","21H2","Intel Xeon E-2388G 3.2GHz 8C","16GB DDR4 ECC","500GB SSD","HP","ProLiant DL360 Gen10","active","IIS/.NET 7 APサーバー"),
        (eid("APM-002","本番環境"),       "sfa-db-prod-01",   "DB",      "sfa-db-prod-01.corp.local",   "40.79.180.12", None,         "Windows Server 2022","21H2","Intel Xeon E-2388G 3.2GHz 8C","32GB DDR4 ECC","2TB SSD","HP","ProLiant DL360 Gen10","active","SQL Server 2022"),
        (eid("APM-002","本番環境"),       "sfa-stor-prod-01", "Storage", "sfa-stor-prod-01.corp.local",  "40.79.180.20", None,         None,None,None,None,"50TB NAS","NetApp","FAS2720","active","共有ストレージ"),
        (eid("APM-002","テスト環境"),     "sfa-ap-test-01",   "Server",  "sfa-ap-test-01.corp.local",   "40.79.181.11", None,         "Windows Server 2022","21H2","Intel Xeon E-2324G 3.1GHz 4C","8GB DDR4","200GB SSD","HP","ProLiant DL360 Gen10","active","テスト用APサーバー"),
        (eid("APM-002","テスト環境"),     "sfa-db-test-01",   "DB",      "sfa-db-test-01.corp.local",   "40.79.181.12", None,         "Windows Server 2022","21H2","Intel Xeon E-2324G 3.1GHz 4C","16GB DDR4","500GB SSD","HP","ProLiant DL360 Gen10","active","SQL Server 2022 テスト用"),
        (eid("APM-003","本番環境"),       "inv-web-prod-01",  "Server",  "inv-prod.corp.local",         "192.168.10.21","192.168.10.200","CentOS 7.9","7.9.2009","Intel Xeon E5-2680v4 2.4GHz 14C","16GB DDR4","1TB HDD","Fujitsu","PRIMERGY RX2530 M4","active","Apache/PHP Webサーバー"),
        (eid("APM-003","本番環境"),       "inv-db-prod-01",   "DB",      "inv-db-prod-01.corp.local",   "192.168.10.22","192.168.10.201","CentOS 7.9","7.9.2009","Intel Xeon E5-2680v4 2.4GHz 14C","32GB DDR4","2TB HDD RAID5","Fujitsu","PRIMERGY RX2540 M4","active","MySQL 8.0"),
        (eid("APM-003","本番環境"),       "inv-stor-prod-01", "Storage", "inv-stor-prod-01.corp.local",  "192.168.10.30","192.168.10.210",None,None,None,None,"20TB NAS","Synology","RS3621RPxs","active","ファイルサーバー"),
        (eid("APM-004","本番環境"),       "exp-ap-prod-01",   "Server",  "expense-prod.corp.local",     "52.194.1.1",   None,         "Amazon Linux 2","2","2vCPU (t3.large)","8GB","100GB SSD","AWS","EC2 t3.large","active","Node.js 18/PM2 本番"),
        (eid("APM-004","本番環境"),       "exp-db-prod-01",   "DB",      "expense-db-prod-01.corp.local","52.194.1.2",  None,         "Amazon Linux 2","2","2vCPU (db.t3.medium)","4GB","100GB SSD","AWS","RDS MySQL 8.0","active","RDS マルチAZ"),
        (eid("APM-005","開発環境"),       "crm-dev-ap-01",    "Server",  "crm-dev.corp.local",          "172.16.0.11",  None,         "Amazon Linux 2","2","2vCPU (t3.small)","4GB","50GB SSD","AWS","EC2 t3.small","active","FastAPI 開発サーバー"),
        (eid("APM-005","開発環境"),       "crm-dev-db-01",    "DB",      "crm-dev-db-01.corp.local",    "172.16.0.12",  None,         "Amazon Linux 2","2","1vCPU (db.t3.micro)","1GB","20GB SSD","AWS","RDS PostgreSQL 15","active","開発用DB"),
    ]
    for (env_id, ci_name, ci_type, hostname, ip_address, bmc_ip,
         os_, os_version, cpu, memory, storage, vendor, model, status, note) in ci_data:
        if env_id is None:
            continue
        cur.execute(
            """INSERT INTO configuration_item
                   (ci_name, ci_type, environment_id, hostname, ip_address, bmc_ip,
                    os, os_version, cpu, memory, storage, vendor, model, status, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [ci_name, ci_type, env_id, hostname, ip_address, bmc_ip,
             os_, os_version, cpu, memory, storage, vendor, model, status, note],
        )

    # ---------- 申請 ----------
    requests = [
        {
            "request_id": "REQ-001", "type": "register",
            "application_id": None,
            "applicant_user_id": user_ids["田中 花子"],
            "applied_at": "2025-06-10 14:23", "status": "pending",
            "approver_user_id": None, "approved_at": None,
            "reason": "購買業務のデジタル化のため新規導入申請",
            "changes": None,
            "app_name": "購買管理システム", "dept": "購買部",
            "biz_owner": "小林 部長", "new_status": "plan",
            "start_plan": "2026-04-01", "end_plan": None,
        },
        {
            "request_id": "REQ-002", "type": "update",
            "application_id": "APM-003",
            "applicant_user_id": user_ids["山田 太郎"],
            "applied_at": "2025-06-11 09:15", "status": "pending",
            "approver_user_id": None, "approved_at": None,
            "reason": "ビジネスオーナー変更（部署異動に伴う）",
            "changes": json.dumps([
                {"label": "ビジネスオーナー", "field": "business_owner",
                 "before": "小林 部長", "after": "田中 部長"},
                {"label": "廃止予定日", "field": "end_plan",
                 "before": "2027-06-30", "after": "2028-03-31"},
            ], ensure_ascii=False),
            "app_name": None, "dept": None, "biz_owner": None,
            "new_status": None, "start_plan": None, "end_plan": None,
        },
        {
            "request_id": "REQ-003", "type": "retire",
            "application_id": "APM-007",
            "applicant_user_id": user_ids["鈴木 一郎"],
            "applied_at": "2025-05-20 16:40", "status": "approved",
            "approver_user_id": user_ids["佐藤 事務局"],
            "approved_at": "2025-05-21 10:00",
            "reason": "新給与システム移行完了のため廃止",
            "changes": None,
            "app_name": None, "dept": None, "biz_owner": None,
            "new_status": None, "start_plan": None, "end_plan": "2026-03-31",
        },
        {
            "request_id": "REQ-004", "type": "update",
            "application_id": "APM-001",
            "applicant_user_id": user_ids["高橋 二郎"],
            "applied_at": "2025-05-15 11:30", "status": "rejected",
            "approver_user_id": user_ids["佐藤 事務局"],
            "approved_at": "2025-05-16 09:00",
            "reason": "廃止予定日の変更申請（理由不十分により却下）",
            "changes": json.dumps([], ensure_ascii=False),
            "app_name": None, "dept": None, "biz_owner": None,
            "new_status": None, "start_plan": None, "end_plan": None,
        },
    ]
    for r in requests:
        cur.execute(
            """INSERT INTO apm_request
                   (request_id, type, application_id, applicant_user_id, applied_at, status,
                    approver_user_id, approved_at, reason, changes,
                    app_name, dept, biz_owner, new_status, start_plan, end_plan)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                r["request_id"], r["type"], r["application_id"],
                r["applicant_user_id"], r["applied_at"], r["status"],
                r["approver_user_id"], r["approved_at"], r["reason"], r["changes"],
                r["app_name"], r["dept"], r["biz_owner"],
                r["new_status"], r["start_plan"], r["end_plan"],
            ],
        )

    # ---------- デマンド ----------
    demands = [
        {
            "demand_id": "DMND1001001",
            "title": "全社工数管理ツールの導入",
            "it_class": "全社共通",
            "category": "戦略投資",
            "domain": "人事・労務",
            "type": "新規導入",
            "start_date": "2026-07-01",
            "due_date": "2027-03-31",
            "submitter_user_id": user_ids["山田 太郎"],
            "department_id": dept_ids["人事部"],
            "manager_user_id": user_ids["佐藤 事務局"],
            "system_owner_user_id": user_ids["山田 太郎"],
            "pm_user_id": user_ids["鈴木 一郎"],
            "description": "全社工数管理ツールを導入し、プロジェクト別・部門別の工数可視化と集計自動化を実現する。",
            "portfolio": "コーポレートIT",
            "program": "生産性向上プログラム",
            "change_type": "新規",
            "purpose": "月次工数集計工数の削減と正確性向上",
            "feasibility": "B:高い",
            "priority": "2 - 高",
            "region": "国内",
            "company": "本社",
            "business_unit": "情報システム部",
            "related_application_id": "APM-001",
            "business_case": "ExcelによるT工数管理は月次集計に1人×3日を要している。専用ツール導入により集計自動化を実現する。",
            "expected_benefit": "月次集計工数を3人日から0.5人日に削減。年間約20人日の削減効果。",
            "target_date": "2027-04-01",
            "estimated_cost": 12000000,
            "requested_budget": 15000000,
            "cost_note": "初期導入費8M、年間ライセンス4M（3年契約）",
            "notes": "HR部門との調整が必要。既存Excelとの移行計画を別途策定。",
            "stage": "screening",
            "reject_reason": None,
            "review_comment": "セキュリティ審査完了。アーキテクチャ審査進行中。",
            "approval_comment": None,
        },
        {
            "demand_id": "DMND1001002",
            "title": "グローバル購買システムの統合",
            "it_class": "グローバル展開",
            "category": "インフラ刷新",
            "domain": "調達・購買",
            "type": "更改・移行",
            "start_date": "2026-10-01",
            "due_date": "2028-09-30",
            "submitter_user_id": user_ids["田中 花子"],
            "department_id": dept_ids["購買部"],
            "manager_user_id": user_ids["佐藤 事務局"],
            "system_owner_user_id": user_ids["田中 花子"],
            "pm_user_id": user_ids["高橋 二郎"],
            "description": "グローバル購買システムを統合し、各拠点バラバラの購買プロセスを標準化する。",
            "portfolio": "グローバルERP",
            "program": "グローバルSCM刷新プログラム",
            "change_type": "更改",
            "purpose": "グローバル購買プロセス標準化とコスト削減",
            "feasibility": "C:中程度",
            "priority": "1 - 最重要",
            "region": "グローバル",
            "company": "グループ全社",
            "business_unit": "購買部",
            "related_application_id": "APM-003",
            "business_case": "現在12拠点で異なるシステムを運用しており、統合により年間運用コストを30%削減見込み。",
            "expected_benefit": "年間運用コスト約2億円削減。標準購買プロセス適用で調達リードタイム20%短縮。",
            "target_date": "2028-10-01",
            "estimated_cost": 85000000,
            "requested_budget": 100000000,
            "cost_note": "SAP Ariba ライセンス50M、移行費用35M",
            "notes": "海外拠点の合意取得が前提条件。法務・コンプライアンス確認必須。",
            "stage": "submitted",
            "reject_reason": None,
            "review_comment": None,
            "approval_comment": None,
        },
        {
            "demand_id": "DMND1001003",
            "title": "営業支援CRM導入（国内営業部門）",
            "it_class": "部門固有",
            "category": "業務改善",
            "domain": "営業・マーケティング",
            "type": "新規導入",
            "start_date": "2025-10-01",
            "due_date": "2026-06-30",
            "submitter_user_id": user_ids["高橋 二郎"],
            "department_id": dept_ids["営業本部"],
            "manager_user_id": user_ids["佐藤 事務局"],
            "system_owner_user_id": user_ids["高橋 二郎"],
            "pm_user_id": user_ids["鈴木 一郎"],
            "description": "国内営業部門向けCRMシステムを導入し、顧客管理・商談管理を一元化する。",
            "portfolio": "営業IT",
            "program": "営業DXプログラム",
            "change_type": "新規",
            "purpose": "商談情報の一元管理と営業活動の可視化",
            "feasibility": "A:確実",
            "priority": "2 - 高",
            "region": "国内",
            "company": "本社",
            "business_unit": "営業本部",
            "related_application_id": "APM-002",
            "business_case": "Excel・メール管理による非効率を解消。Salesforceで商談管理・予実管理を実現。",
            "expected_benefit": "営業活動の可視化により受注率10%向上。週次レポート作成工数を2時間から0に削減。",
            "target_date": "2026-07-01",
            "estimated_cost": 8000000,
            "requested_budget": 10000000,
            "cost_note": "Salesforceライセンス5M/年、カスタマイズ3M",
            "notes": "全タスク完了済み。プロジェクト化済み。",
            "stage": "approved",
            "reject_reason": None,
            "review_comment": "全審査項目クリア。承認申請へ移行。",
            "approval_comment": "承認。プロジェクト化を指示。",
        },
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
                related_application_id, business_case, expected_benefit,
                target_date, estimated_cost, requested_budget, cost_note, notes,
                stage, reject_reason, review_comment, approval_comment)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            [
                d["demand_id"], d["title"], d["it_class"], d["category"], d["domain"], d["type"],
                d["start_date"], d["due_date"],
                d["submitter_user_id"], d["department_id"], d["manager_user_id"],
                d["system_owner_user_id"], d["pm_user_id"],
                d["description"], d["portfolio"], d["program"], d["change_type"], d["purpose"],
                d["feasibility"], d["priority"], d["region"], d["company"], d["business_unit"],
                d["related_application_id"], d["business_case"], d["expected_benefit"],
                d["target_date"], d["estimated_cost"], d["requested_budget"], d["cost_note"], d["notes"],
                d["stage"], d["reject_reason"], d["review_comment"], d["approval_comment"],
            ],
        )

    # ---------- デマンドタスク ----------
    demand_tasks = [
        # DMND1001001 (screening)
        ("DMNTSK4001001", "DMND1001001", "セキュリティ審査",       "2026-08-31", user_ids["佐藤 事務局"], "2 - 高",    "closed",     "セキュリティ要件を確認済み。問題なし。", 1, "セキュリティポリシー準拠確認"),
        ("DMNTSK4001002", "DMND1001001", "アーキテクチャ審査",     "2026-09-30", user_ids["鈴木 一郎"],  "2 - 高",    "inprogress", "クラウドvs.オンプレ検討中",         1, "技術アーキテクチャの妥当性確認"),
        ("DMNTSK4001003", "DMND1001001", "企画審査",               "2026-10-31", user_ids["山田 太郎"],  "3 - 中",    "open",       None,                                  1, "ビジネスケースと費用対効果の確認"),
        ("DMNTSK4001004", "DMND1001001", "投資審査",               "2026-11-30", user_ids["佐藤 事務局"], "1 - 最重要", "open",       None,                                  1, "投資委員会への上程・承認取得"),
        # DMND1001002 (submitted)
        ("DMNTSK4002001", "DMND1001002", "セキュリティ審査",       "2026-12-31", user_ids["佐藤 事務局"], "1 - 最重要", "open",       None, 1, "グローバルセキュリティ基準適合確認"),
        ("DMNTSK4002002", "DMND1001002", "アーキテクチャ審査",     "2027-01-31", user_ids["高橋 二郎"],  "1 - 最重要", "open",       None, 1, "統合アーキテクチャ設計の妥当性確認"),
        # DMND1001003 (approved - all closed)
        ("DMNTSK4003001", "DMND1001003", "セキュリティ審査",       "2025-11-30", user_ids["佐藤 事務局"], "2 - 高",    "closed",     "Salesforceセキュリティ審査完了。",    1, "SaaS利用基準の確認"),
        ("DMNTSK4003002", "DMND1001003", "アーキテクチャ審査",     "2025-12-31", user_ids["鈴木 一郎"],  "2 - 高",    "closed",     "API連携設計確認済み。",               1, "既存システムとの連携設計確認"),
        ("DMNTSK4003003", "DMND1001003", "企画審査",               "2026-01-31", user_ids["高橋 二郎"],  "3 - 中",    "closed",     "ビジネスケース承認。",                1, "ビジネスケース確認"),
        ("DMNTSK4003004", "DMND1001003", "投資審査",               "2026-02-28", user_ids["佐藤 事務局"], "1 - 最重要", "closed",     "投資委員会承認取得。",                1, "投資委員会承認"),
    ]
    for (task_id, demand_id, name, due_date, assignee_id, priority, state, comment, ai_gen, rationale) in demand_tasks:
        cur.execute(
            """INSERT INTO demand_task
               (task_id, demand_id, name, due_date, assignee_user_id, priority, state, comment, ai_generated, rationale)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            [task_id, demand_id, name, due_date, assignee_id, priority, state, comment, ai_gen, rationale],
        )

    # ---------- プロジェクト ----------
    cur.execute(
        """INSERT INTO project (project_id, demand_id, title, status, created_date)
           VALUES (?,?,?,?,?)""",
        ["PROJ00001", "DMND1001003", "営業支援CRM導入（国内営業部門）", "active", "2026-03-01"],
    )

    conn.commit()
    conn.close()
    print("✓ シードデータを投入しました")
    print(f"  部署: {len(departments)}件, ユーザー: {len(users)}件")
    print(f"  アプリケーション: {len(apps)}件 (インフラ含む), 環境: {len(envs)}件")
    print(f"  CI: {len(ci_data)}件, 依存関係: {len(deps)}件, 申請: {len(requests)}件")
    print(f"  デマンド: {len(demands)}件, タスク: {len(demand_tasks)}件")


if __name__ == "__main__":
    seed()
