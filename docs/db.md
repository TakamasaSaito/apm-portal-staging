# DBスキーマ設計

## ERD（Mermaid）

```mermaid
erDiagram
    department {
        int department_id PK
        text department_name
    }
    user {
        int user_id PK
        text user_name
        int department_id FK
        text role
        text login_id
        text password_hash
    }
    application {
        text application_id PK
        text application_name
        int owner_department_id FK
        text status
        text vendor
        text business_owner
        text system_owner
        text ops_manager
        text dev_manager
        text start_plan
        text start_actual
        text end_plan
        text end_actual
        text app_category
        int portfolio_area
        text migration_target_id FK
        int annual_cost_million
        int is_infrastructure
    }
    environment {
        int environment_id PK
        text env_type
        text location
        text ip
        text host
        text os
        text middleware
        text cpu_mem
        text storage
    }
    configuration_item {
        int ci_id PK
        text ci_name
        text ci_type
        text hostname
        text ip_address
        text bmc_ip
        text os
        text os_version
        text cpu
        text memory
        text storage
        text vendor
        text model
        text status
        text note
    }
    relation_type {
        int relation_type_id PK
        text type_name
        text parent_label
        text child_label
    }
    cmdb_rel_ci {
        int rel_id PK
        text parent_table
        text parent_id
        text child_table
        text child_id
        int relation_type_id FK
        text note
        datetime created_at
    }
    business_capability {
        text capability_id PK
        text capability_name
        text parent_id FK
        int level
        text scope
        int sort_order
    }
    application_dependency {
        int dependency_id PK
        text app_id FK
        text depends_on_app_id FK
        text dependency_type
        text note
        text migration_status
        date migration_due_date
        text migration_note
    }
    demand {
        text demand_id PK
        text title
        text stage
        int submitter_user_id FK
        int department_id FK
        int manager_user_id FK
        int pm_user_id FK
        int estimated_cost
        int score
        text investment_class
        int capital_expense
        int operating_expense
        int financial_benefit
        real roi_percent
        int npv
        real irr
        int capital_budget
        int operating_budget
        real discount_rate
        int demand_actual_cost
    }
    demand_application {
        int id PK
        text demand_id FK
        text application_id FK
        text relation_note
    }
    demand_task {
        text task_id PK
        text demand_id FK
        text name
        text state
        int assignee_user_id FK
        text priority
        date due_date
        text comment
        int ai_generated
        text rationale
    }
    cost_plan {
        int cost_plan_id PK
        text demand_id FK
        int fiscal_year
        text fiscal_period
        text cost_type
        int unit_cost
        int quantity
        int planned_cost
        int actual_cost
        text note
    }
    project {
        text project_id PK
        text demand_id FK
        text title
        text status
        int manager_user_id FK
        text portfolio
        text description
        date created_date
    }
    apm_request {
        text request_id PK
        text type
        text application_id FK
        int applicant_user_id FK
        text applied_at
        text status
        int approver_user_id FK
        text approved_at
        text reason
        text changes
        text app_name
        text dept
        text biz_owner
        text new_status
        text start_plan
        text end_plan
        text app_category
    }

    department ||--o{ user : "department_id"
    department ||--o{ application : "owner_department_id"
    department ||--o{ demand : "department_id"
    user ||--o{ demand : "submitter_user_id"
    user ||--o{ demand : "manager_user_id"
    user ||--o{ demand_task : "assignee_user_id"
    user ||--o{ project : "manager_user_id"
    user ||--o{ apm_request : "applicant_user_id"
    user ||--o{ apm_request : "approver_user_id"
    application ||--o{ application_dependency : "app_id"
    application ||--o{ application_dependency : "depends_on_app_id"
    application ||--o| application : "migration_target_id"
    application ||--o{ demand_application : "application_id"
    application ||--o{ apm_request : "application_id"
    demand ||--o{ demand_application : "demand_id"
    demand ||--o{ demand_task : "demand_id"
    demand ||--o{ cost_plan : "demand_id"
    demand ||--o| project : "demand_id"
    relation_type ||--o{ cmdb_rel_ci : "relation_type_id"
    business_capability ||--o| business_capability : "parent_id"
```

## テーブル一覧

| テーブル | 主な用途 |
|---------|---------|
| department | 部門マスター |
| user | ユーザー・認証情報 |
| application | システム（アプリケーション）台帳 |
| environment | サーバー環境 |
| configuration_item | 構成アイテム（CI） |
| relation_type | CMDBリレーション種別マスター |
| cmdb_rel_ci | アプリ↔環境↔CIの汎用リレーション |
| business_capability | ビジネスケイパビリティ（L1/L2） |
| application_dependency | アプリ間依存関係 |
| demand | デマンド（IT投資申請） |
| demand_application | デマンド↔システム紐付け |
| demand_task | デマンドに紐づくタスク |
| cost_plan | コスト計画（計画/実績） |
| project | デマンドから生成されたプロジェクト |
| apm_request | システム変更申請 |

## 設計上の重要事項

- environment・CIのFKは廃止済み。cmdb_rel_ci経由でのみ親子関係を管理
- ケイパビリティ↔システムの紐付けはcmdb_rel_ci（type_name='realizes'）を流用
- CIリレーション一覧画面ではrealizes除外表示

## relation_type マスター

| type_name | parent_label | child_label | 用途 |
|-----------|-------------|-------------|------|
| has_environment | 環境を持つ | 環境である | application→environment |
| has_ci | 構成情報を持つ | 構成情報である | environment→CI |
| realizes | ケイパビリティ | 実現システム | capability→application |
