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

    # テーブルが存在しない場合は作成
    cur.executescript("""
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
        "ALTER TABLE apm_request ADD COLUMN app_category TEXT",
    ):
        try:
            cur.execute(stmt)
        except Exception:
            pass

    # 既存データクリア
    for table in ["apm_request", "environment", "application", "user", "department"]:
        cur.execute(f"DELETE FROM {table}")

    # ---------- 部署 ----------
    departments = ["人事部", "営業本部", "購買部", "経理部", "総務部", "情報システム部"]
    dept_ids: dict[str, int] = {}
    for d in departments:
        cur.execute("INSERT INTO department (department_name) VALUES (?)", [d])
        dept_ids[d] = cur.lastrowid

    # ---------- ユーザー ----------
    # user_id=1: 申請者ユーザー（login_id=user / password=user）
    # user_id=2: 事務局ユーザー（login_id=admin / password=admin）
    users = [
        ("申請者ユーザー", "情報システム部", "applicant", "user",  _hash("user")),
        ("事務局ユーザー", "情報システム部", "admin",     "admin", _hash("admin")),
        ("田中 花子",   "購買部",       "applicant", None, None),
        ("山田 太郎",   "人事部",       "applicant", None, None),
        ("鈴木 一郎",   "人事部",       "applicant", None, None),
        ("高橋 二郎",   "営業本部",     "applicant", None, None),
        ("佐藤 事務局", "情報システム部", "admin",     None, None),
    ]
    user_ids: dict[str, int] = {}
    for name, dept, role, login_id, password_hash in users:
        cur.execute(
            "INSERT INTO user (user_name, department_id, role, login_id, password_hash) VALUES (?, ?, ?, ?, ?)",
            [name, dept_ids[dept], role, login_id, password_hash],
        )
        user_ids[name] = cur.lastrowid

    # ---------- アプリケーション ----------
    apps = [
        ("APM-001", "人事管理システム",       "人事部",   "running",
         "田中 部長", "山田 課長", "鈴木 主任", "佐藤 主任",
         "2021-04-01", "2021-04-01", "2028-03-31", None,
         "HRM（人事・労務・給与）"),
        ("APM-002", "営業支援システム（SFA）", "営業本部", "running",
         "高橋 部長", "伊藤 課長", "渡辺 主任", "中村 主任",
         "2020-10-01", "2020-10-15", "2027-09-30", None,
         "CRM（顧客管理・営業支援）"),
        ("APM-003", "在庫管理システム",       "購買部",   "running",
         "小林 部長", "加藤 課長", "吉田 主任", "山本 主任",
         "2019-07-01", "2019-07-01", "2026-06-30", None,
         "SCM（サプライチェーン・購買・在庫）"),
        ("APM-004", "経費精算システム",       "経理部",   "running",
         "松本 部長", "井上 課長", "木村 主任", "林 主任",
         "2022-01-01", "2022-02-01", None, None,
         "Finance（経理・財務・予算）"),
        ("APM-005", "顧客管理システム（CRM）", "営業本部", "dev",
         "高橋 部長", "石川 課長", "（未定）", "前田 主任",
         "2025-10-01", None, None, None,
         "CRM（顧客管理・営業支援）"),
        ("APM-006", "文書管理システム",       "総務部",   "plan",
         "清水 部長", "（未定）", "（未定）", "（未定）",
         "2026-04-01", None, None, None,
         "Document Management（文書・コンテンツ管理）"),
        ("APM-007", "旧給与計算システム",     "人事部",   "retire",
         "田中 部長", "（退任）", "（退任）", "（退任）",
         "2010-04-01", "2010-04-01", "2023-03-31", "2023-03-31",
         "HRM（人事・労務・給与）"),
        ("APM-008", "購買管理システム",       "購買部",   "running",
         "小林 部長", "加藤 課長", "吉田 主任", "山本 主任",
         "2018-04-01", "2018-04-01", "2028-03-31", None,
         "SCM（サプライチェーン・購買・在庫）"),
        ("APM-009", "法務契約管理システム",   "総務部",   "running",
         "清水 部長", "藤田 課長", "岡田 主任", "中島 主任",
         "2020-07-01", "2020-07-15", "2027-06-30", None,
         "Legal / Compliance（法務・コンプライアンス）"),
        ("APM-010", "マーケティング自動化ツール", "営業本部", "running",
         "高橋 部長", "石川 課長", "前田 主任", "村田 主任",
         "2021-10-01", "2021-11-01", "2028-09-30", None,
         "Marketing（マーケティング）"),
        ("APM-011", "ITサービス管理システム（ITSM）", "情報システム部", "running",
         "佐藤 部長", "田中 課長", "鈴木 主任", "高橋 主任",
         "2019-04-01", "2019-04-01", "2029-03-31", None,
         "ITSM / ITOM（ITサービス・運用管理）"),
        ("APM-012", "ネットワーク管理システム", "情報システム部", "running",
         "佐藤 部長", "山田 課長", "井上 主任", "木村 主任",
         "2017-10-01", "2017-10-01", "2027-09-30", None,
         "Network（ネットワーク）"),
        ("APM-013", "セキュリティ管理プラットフォーム", "情報システム部", "running",
         "佐藤 部長", "渡辺 課長", "伊藤 主任", "中村 主任",
         "2022-04-01", "2022-05-01", "2030-03-31", None,
         "Security（セキュリティ管理）"),
        ("APM-014", "サーバー監視システム",   "情報システム部", "running",
         "佐藤 部長", "加藤 課長", "吉田 主任", "松本 主任",
         "2016-07-01", "2016-07-01", "2026-06-30", None,
         "Monitoring（監視・ログ管理）"),
        ("APM-015", "クラウド基盤管理ポータル", "情報システム部", "running",
         "佐藤 部長", "林 課長", "清水 主任", "山口 主任",
         "2020-01-01", "2020-02-01", "2030-12-31", None,
         "Cloud Platform（クラウド基盤）"),
        ("APM-016", "BIレポーティングツール", "経理部",   "running",
         "松本 部長", "井上 課長", "木村 主任", "林 主任",
         "2021-07-01", "2021-07-01", "2028-06-30", None,
         "BI / Analytics（分析・レポート）"),
        ("APM-017", "データ連携基盤（ETL）",  "情報システム部", "running",
         "佐藤 部長", "田中 課長", "鈴木 主任", "高橋 主任",
         "2019-10-01", "2019-10-01", "2027-09-30", None,
         "Data Integration（データ連携・ETL）"),
        ("APM-018", "グループウェア",         "総務部",   "running",
         "清水 部長", "藤田 課長", "岡田 主任", "中島 主任",
         "2015-04-01", "2015-04-01", "2027-03-31", None,
         "Collaboration（グループウェア・社内コミュニケーション）"),
        ("APM-019", "基幹ERPシステム",        "経理部",   "running",
         "松本 部長", "佐々木 課長", "大野 主任", "石田 主任",
         "2014-04-01", "2014-04-01", "2029-03-31", None,
         "ERP（基幹業務）"),
        ("APM-020", "採用管理システム",       "人事部",   "running",
         "田中 部長", "山田 課長", "鈴木 主任", "中川 主任",
         "2023-04-01", "2023-04-01", "2030-03-31", None,
         "HRM（人事・労務・給与）"),
        ("APM-021", "旧在庫管理システム",     "購買部",   "retire",
         "小林 部長", "（退任）", "（退任）", "（退任）",
         "2008-04-01", "2008-04-01", "2019-06-30", "2019-06-30",
         "SCM（サプライチェーン・購買・在庫）"),
        ("APM-022", "旧グループウェア（Notes）", "総務部", "retire",
         "清水 部長", "（退任）", "（退任）", "（退任）",
         "2005-04-01", "2005-04-01", "2015-03-31", "2015-03-31",
         "Collaboration（グループウェア・社内コミュニケーション）"),
        ("APM-023", "ERP刷新プロジェクト",    "経理部",   "dev",
         "松本 部長", "佐々木 課長", "（未定）", "大野 主任",
         "2026-10-01", None, None, None,
         "ERP（基幹業務）"),
        ("APM-024", "データ分析基盤刷新",     "情報システム部", "plan",
         "佐藤 部長", "（未定）", "（未定）", "（未定）",
         "2027-04-01", None, None, None,
         "BI / Analytics（分析・レポート）"),
        ("APM-025", "予算管理システム",       "経理部",   "order",
         "松本 部長", "井上 課長", "（未定）", "石田 主任",
         "2025-12-01", None, None, None,
         "Finance（経理・財務・予算）"),
        ("APM-026", "DBaaSプラットフォーム",  "情報システム部", "running",
         "佐藤 部長", "渡辺 課長", "伊藤 主任", "村山 主任",
         "2021-04-01", "2021-04-01", "2031-03-31", None,
         "Database（データベース）"),
        ("APM-027", "コンプライアンス管理ツール", "総務部", "running",
         "清水 部長", "藤田 課長", "岡田 主任", "西村 主任",
         "2023-07-01", "2023-07-01", "2030-06-30", None,
         "Legal / Compliance（法務・コンプライアンス）"),
    ]
    for (app_id, name, dept, status,
         biz, sys_o, ops, dev,
         start_p, start_a, end_p, end_a, app_cat) in apps:
        cur.execute(
            """
            INSERT INTO application
                (application_id, application_name, owner_department_id, status,
                 business_owner, system_owner, ops_manager, dev_manager,
                 start_plan, start_actual, end_plan, end_actual, app_category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [app_id, name, dept_ids[dept], status,
             biz, sys_o, ops, dev,
             start_p, start_a, end_p, end_a, app_cat],
        )

    # ---------- 環境 ----------
    envs = [
        ("APM-001", "本番環境",       "東京DC",               "10.1.1.10",     "hr-prod.corp.local",      "RHEL 8.6",           "Tomcat 10/Java17",      "8vCPU/32GB", "1TB SSD"),
        ("APM-001", "ステージング環境", "東京DC",               "10.1.2.10",     "hr-stg.corp.local",       "RHEL 8.6",           "Tomcat 10/Java17",      "4vCPU/16GB", "500GB SSD"),
        ("APM-001", "開発環境",       "AWS ap-northeast-1",   "172.31.0.10",   "hr-dev.corp.local",       "RHEL 8.6",           "Tomcat 10/Java17",      "2vCPU/8GB",  "200GB SSD"),
        ("APM-002", "本番環境",       "Azure Japan East",     "40.79.180.x",   "sfa-prod.corp.local",     "Windows Server 2022", ".NET 7/IIS",            "8vCPU/16GB", "500GB SSD"),
        ("APM-002", "テスト環境",     "Azure Japan East",     "40.79.181.x",   "sfa-test.corp.local",     "Windows Server 2022", ".NET 7/IIS",            "4vCPU/8GB",  "200GB SSD"),
        ("APM-003", "本番環境",       "大阪DC",               "192.168.10.20", "inv-prod.corp.local",     "CentOS 7.9",          "Apache/PHP 8.1",        "4vCPU/16GB", "2TB HDD"),
        ("APM-003", "ステージング環境", "大阪DC",               "192.168.11.20", "inv-stg.corp.local",      "CentOS 7.9",          "Apache/PHP 8.1",        "2vCPU/8GB",  "500GB HDD"),
        ("APM-003", "開発環境",       "大阪DC",               "192.168.12.20", "inv-dev.corp.local",      "CentOS 7.9",          "Apache/PHP 8.1",        "2vCPU/4GB",  "200GB HDD"),
        ("APM-004", "本番環境",       "AWS ap-northeast-1",   "52.194.x.x",   "expense-prod.corp.local", "Amazon Linux 2",      "Node.js 18/PM2",        "4vCPU/8GB",  "200GB SSD"),
        ("APM-004", "開発環境",       "AWS ap-northeast-1",   "52.195.x.x",   "expense-dev.corp.local",  "Amazon Linux 2",      "Node.js 18/PM2",        "2vCPU/4GB",  "100GB SSD"),
        ("APM-005", "開発環境",       "AWS ap-northeast-1",   "（未割当）",    "crm-dev.corp.local",      "Amazon Linux 2",      "Python 3.11/FastAPI",   "2vCPU/4GB",  "100GB SSD"),
    ]
    for row in envs:
        cur.execute(
            """
            INSERT INTO environment
                (application_id, env_type, location, ip, host, os, middleware, cpu_mem, storage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            list(row),
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
                 "before": "2026-06-30", "after": "2027-03-31"},
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
            "new_status": None, "start_plan": None, "end_plan": "2023-03-31",
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
            """
            INSERT INTO apm_request
                (request_id, type, application_id, applicant_user_id, applied_at, status,
                 approver_user_id, approved_at, reason, changes,
                 app_name, dept, biz_owner, new_status, start_plan, end_plan)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                r["request_id"], r["type"], r["application_id"],
                r["applicant_user_id"], r["applied_at"], r["status"],
                r["approver_user_id"], r["approved_at"], r["reason"], r["changes"],
                r["app_name"], r["dept"], r["biz_owner"],
                r["new_status"], r["start_plan"], r["end_plan"],
            ],
        )

    conn.commit()
    conn.close()
    print("✓ シードデータを投入しました")
    print(f"  部署: {len(departments)}件, ユーザー: {len(users)}件")
    print(f"  アプリケーション: {len(apps)}件, 環境: {len(envs)}件, 申請: {len(requests)}件")


if __name__ == "__main__":
    seed()
