# APIエンドポイント一覧

ベースURL：`/api`  
認証：`Authorization: Bearer <JWT>` ヘッダー（`/api/auth/login` のみ不要）

## 認証

| メソッド | パス | 説明 |
|---------|------|------|
| POST | /api/auth/login | ログイン（JWT取得） |

## ダッシュボード（prefix: /api/dashboard）

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/dashboard/summary | KPI集計（システム数・デマンド数・コスト等） |
| GET | /api/dashboard/retirement-readiness | ライフサイクル・退役準備状況 |
| GET | /api/dashboard/bubble | Demand Workbenchバブルデータ |

## アプリケーション（prefix: /api）

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/applications | システム一覧（フィルタ対応） |
| GET | /api/applications/{app_id} | システム詳細 |
| PUT | /api/applications/{app_id} | システム更新 |
| GET | /api/applications/{app_id}/overview | システム全体像（環境・CI・依存関係） |
| GET | /api/stats | 統計サマリー |
| GET | /api/application-dependencies | アプリ依存関係一覧 |
| PUT | /api/application-dependencies/{dep_id} | 依存関係更新（移行ステータス等） |
| GET | /api/departments | 部門一覧 |

## ケイパビリティ（prefix: /api/capabilities）

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/capabilities/matrix | マトリクス表示用データ（L1/L2+紐づくシステム） |
| GET | /api/capabilities | ケイパビリティ全件一覧 |
| POST | /api/capabilities | ケイパビリティ新規作成 |
| PUT | /api/capabilities/{capability_id} | ケイパビリティ更新 |
| DELETE | /api/capabilities/{capability_id} | ケイパビリティ削除 |
| GET | /api/capabilities/{capability_id}/applications | ケイパビリティに紐づくシステム一覧 |
| POST | /api/capabilities/{capability_id}/applications | システム紐付け追加 |
| DELETE | /api/capabilities/{capability_id}/applications/{app_id} | システム紐付け削除 |

## 環境（prefix: /api）

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/environments | 環境一覧 |
| POST | /api/environments | 環境新規作成 |
| PUT | /api/environments/{env_id} | 環境更新 |
| DELETE | /api/environments/{env_id} | 環境削除 |

## CI（prefix: /api/ci）

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/ci | CI一覧 |
| GET | /api/ci/{ci_id} | CI詳細 |
| POST | /api/ci | CI新規作成 |
| PUT | /api/ci/{ci_id} | CI更新 |
| DELETE | /api/ci/{ci_id} | CI削除 |

## CMDB（prefix: /api）

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/relation-types | リレーション種別マスター一覧 |
| GET | /api/cmdb-relations | CMDBリレーション一覧（realizes除外） |
| POST | /api/cmdb-relations | CMDBリレーション追加 |
| PUT | /api/cmdb-relations/{rel_id} | CMDBリレーション更新 |
| DELETE | /api/cmdb-relations/{rel_id} | CMDBリレーション削除 |

## デマンド・プロジェクト（prefix: /api）

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/demands | デマンド一覧（ステージフィルタ対応） |
| GET | /api/demands/{demand_id} | デマンド詳細 |
| POST | /api/demands | デマンド新規起票 |
| PUT | /api/demands/{demand_id} | デマンド更新 |
| PUT | /api/demands/{demand_id}/stage | ステージ変更 |
| POST | /api/demands/{demand_id}/approve | 承認 |
| POST | /api/demands/{demand_id}/reject | 却下 |
| GET | /api/demands/{demand_id}/tasks | タスク一覧 |
| POST | /api/demands/{demand_id}/tasks | タスク追加 |
| PUT | /api/demands/{demand_id}/tasks/{task_id} | タスク更新 |
| GET | /api/demands/{demand_id}/applications | 紐づくシステム一覧 |
| POST | /api/demands/{demand_id}/applications | システム紐付け追加 |
| DELETE | /api/demands/{demand_id}/applications/{application_id} | システム紐付け削除 |
| GET | /api/demands/{demand_id}/cost-plans | コスト計画一覧 |
| POST | /api/demands/{demand_id}/cost-plans | コスト計画追加 |
| PUT | /api/cost-plans/{cost_plan_id} | コスト計画更新 |
| DELETE | /api/cost-plans/{cost_plan_id} | コスト計画削除 |
| GET | /api/projects | プロジェクト一覧 |
| POST | /api/projects | プロジェクト新規作成 |
| GET | /api/projects/{project_id} | プロジェクト詳細 |

## 申請ワークフロー（prefix: /api）

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/requests | 申請一覧（statusフィルタ対応） |
| POST | /api/requests | 申請新規作成 |
| PUT | /api/requests/{req_id}/approve | 申請承認 |
| PUT | /api/requests/{req_id}/reject | 申請却下 |
