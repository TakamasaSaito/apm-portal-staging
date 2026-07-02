# ITアセット管理機能 設計書

## 概要

システム（application）・環境（environment）・構成アイテム（CI）の3層構造でITアセットを管理する機能。

## 管理階層

```
application（システム）
  └── environment（環境：本番/検証/開発等）
        └── configuration_item（CI：サーバー・ネットワーク機器等）
```

## リレーション管理

全てのツリー関係を `cmdb_rel_ci` テーブルで管理（FK廃止済み）：

| リレーション | parent_table | child_table | type_name |
|-------------|-------------|-------------|-----------|
| application → environment | application | environment | has_environment |
| environment → CI | environment | configuration_item | has_ci |
| capability → application | business_capability | application | realizes |

### cmdb_rel_ci の参照方法

```sql
-- あるシステムに紐づく環境一覧
SELECT e.* FROM environment e
JOIN cmdb_rel_ci r ON r.child_table='environment' AND r.child_id=CAST(e.environment_id AS TEXT)
JOIN relation_type rt ON rt.relation_type_id=r.relation_type_id
WHERE r.parent_table='application' AND r.parent_id=? AND rt.type_name='has_environment';
```

## application テーブル（主要フィールド）

| カラム | 説明 |
|--------|------|
| application_id | UUID形式のPK |
| application_name | システム名称 |
| status | plan / active / retiring / retired |
| owner_department_id | 所管部門 |
| business_owner | ビジネスオーナー（氏名テキスト） |
| system_owner | システムオーナー（氏名テキスト） |
| app_category | アプリカテゴリ |
| portfolio_area | ポートフォリオ区分（整数） |
| annual_cost_million | 年間コスト（百万円） |
| is_infrastructure | インフラフラグ（0/1） |
| migration_target_id | 移行先システムID（FK自己参照） |

## システム全体像ビュー

`GET /api/applications/{app_id}/overview` が返すデータを使って3モードで表示：

| モード | 説明 |
|--------|------|
| リスト | 環境・CI・依存関係をテーブル形式で表示 |
| ツリー | application→environment→CIの階層ツリー表示 |
| ネットワーク | システム間依存関係をグラフ表示 |

## 申請ワークフロー

システム情報の変更は `apm_request` 経由で管理：

| 申請種別 (type) | 内容 |
|---------------|------|
| new | 新規システム登録申請 |
| update | システム情報更新申請 |
| retire | 廃止申請 |

フロー：申請者が `POST /api/requests` → 事務局が `PUT /api/requests/{id}/approve` → `application` テーブル自動更新

## application_dependency テーブル

システム間の依存関係と移行計画を管理：

| カラム | 説明 |
|--------|------|
| dependency_type | 依存種別（data / api / batch等） |
| migration_status | not_planned / planned / completed |
| migration_due_date | 移行予定日 |
| migration_note | 移行メモ |

## environment テーブル（主要フィールド）

| カラム | 説明 |
|--------|------|
| env_type | 環境種別（production / staging / development等） |
| location | 設置場所 |
| ip | IPアドレス |
| host | ホスト名 |
| os | OS情報 |
| middleware | ミドルウェア情報 |
| cpu_mem | CPU・メモリ情報 |
| storage | ストレージ情報 |

## configuration_item テーブル（主要フィールド）

| カラム | 説明 |
|--------|------|
| ci_name | CI名称 |
| ci_type | CI種別（server / network / storage等） |
| hostname | ホスト名 |
| ip_address | IPアドレス |
| bmc_ip | BMC/iLO等管理IPアドレス |
| status | active / maintenance / decommissioned |
