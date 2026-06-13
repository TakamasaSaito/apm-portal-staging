"""初期データ投入スクリプト。既存データをクリアして再投入する。"""
import sqlite3
import json
import os

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
    role          TEXT NOT NULL DEFAULT 'applicant'
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
    end_actual          TEXT
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
    end_plan          TEXT
);
    """)

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
    # user_id=1: 申請者ユーザー（デモ用申請者）
    # user_id=2: 事務局ユーザー（デモ用承認者）
    users = [
        ("申請者ユーザー", "情報システム部", "applicant"),
        ("事務局ユーザー", "情報システム部", "admin"),
        ("田中 花子",   "購買部",       "applicant"),
        ("山田 太郎",   "人事部",       "applicant"),
        ("鈴木 一郎",   "人事部",       "applicant"),
        ("高橋 二郎",   "営業本部",     "applicant"),
        ("佐藤 事務局", "情報システム部", "admin"),
    ]
    user_ids: dict[str, int] = {}
    for name, dept, role in users:
        cur.execute(
            "INSERT INTO user (user_name, department_id, role) VALUES (?, ?, ?)",
            [name, dept_ids[dept], role],
        )
        user_ids[name] = cur.lastrowid

    # ---------- アプリケーション ----------
    apps = [
        ("APM-001", "人事管理システム",       "人事部",   "running",
         "田中 部長", "山田 課長", "鈴木 主任", "佐藤 主任",
         "2021-04-01", "2021-04-01", "2028-03-31", None),
        ("APM-002", "営業支援システム（SFA）", "営業本部", "running",
         "高橋 部長", "伊藤 課長", "渡辺 主任", "中村 主任",
         "2020-10-01", "2020-10-15", "2027-09-30", None),
        ("APM-003", "在庫管理システム",       "購買部",   "running",
         "小林 部長", "加藤 課長", "吉田 主任", "山本 主任",
         "2019-07-01", "2019-07-01", "2026-06-30", None),
        ("APM-004", "経費精算システム",       "経理部",   "running",
         "松本 部長", "井上 課長", "木村 主任", "林 主任",
         "2022-01-01", "2022-02-01", None, None),
        ("APM-005", "顧客管理システム（CRM）", "営業本部", "dev",
         "高橋 部長", "石川 課長", "（未定）", "前田 主任",
         "2025-10-01", None, None, None),
        ("APM-006", "文書管理システム",       "総務部",   "plan",
         "清水 部長", "（未定）", "（未定）", "（未定）",
         "2026-04-01", None, None, None),
        ("APM-007", "旧給与計算システム",     "人事部",   "retire",
         "田中 部長", "（退任）", "（退任）", "（退任）",
         "2010-04-01", "2010-04-01", "2023-03-31", "2023-03-31"),
    ]
    for (app_id, name, dept, status,
         biz, sys_o, ops, dev,
         start_p, start_a, end_p, end_a) in apps:
        cur.execute(
            """
            INSERT INTO application
                (application_id, application_name, owner_department_id, status,
                 business_owner, system_owner, ops_manager, dev_manager,
                 start_plan, start_actual, end_plan, end_actual)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [app_id, name, dept_ids[dept], status,
             biz, sys_o, ops, dev,
             start_p, start_a, end_p, end_a],
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
