# Business Portfolio機能 設計書

## 概要

ビジネスケイパビリティ（業務体系）とシステムを多対多で紐付け、同一ケイパビリティへの重複システムを検知する機能。

## データ設計

`business_capability` テーブル（自己参照、level 1/2の2階層）と `cmdb_rel_ci`（realizes）の組み合わせで実現。

### business_capability テーブル

| カラム | 型 | 説明 |
|--------|-----|------|
| capability_id | TEXT PK | L1: "L1-01" / L2: "L2-01-01" 形式 |
| capability_name | TEXT | ケイパビリティ名称 |
| parent_id | TEXT FK | L2の場合は親L1のID。L1はNULL |
| level | INTEGER | 1 または 2 |
| scope | TEXT | 表示用スコープ情報（判定には未使用） |
| sort_order | INTEGER | 表示順 |

### リレーション管理

ケイパビリティ↔システムの紐付けは `cmdb_rel_ci` を流用：

```
cmdb_rel_ci.parent_table = 'business_capability'
cmdb_rel_ci.parent_id    = capability_id
cmdb_rel_ci.child_table  = 'application'
cmdb_rel_ci.child_id     = application_id
cmdb_rel_ci.relation_type_id = (realizes の relation_type_id)
```

## 判定ロジック

| 紐づくシステム数 | 判定 | 表示 |
|----------------|------|------|
| 0件 | 未対応 | グレー |
| 1件 | 正常 | 緑 |
| 2件以上 | 重複候補 | オレンジ・⚠ |

scopeは判定に使わず表示のみ。

## 画面構成

### Business Portfolio（マトリクス表示）
- L1カードを横並びに表示
- 各L1カード内にL2行を縦リスト表示
- 各L2行に紐づくシステム数バッジを表示（重複時はオレンジ）
- バッジクリックで紐づくシステム名のポップアップ

### ケイパビリティ登録
- L1新規追加フォーム
- L2新規追加フォーム（親L1選択）
- ケイパビリティ↔システム紐付け管理
- 全ケイパビリティ一覧テーブル（L1ダミー行を除外して表示）

## APIエンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/capabilities/matrix | マトリクス表示用データ |
| GET | /api/capabilities | ケイパビリティ全件一覧 |
| POST | /api/capabilities | 新規作成 |
| PUT | /api/capabilities/{id} | 更新 |
| DELETE | /api/capabilities/{id} | 削除 |
| GET | /api/capabilities/{id}/applications | 紐づくシステム一覧 |
| POST | /api/capabilities/{id}/applications | システム紐付け追加 |
| DELETE | /api/capabilities/{id}/applications/{app_id} | システム紐付け削除 |

## 既知の制約・仕様

- CIリレーション一覧画面では realizes を除外表示（has_environment / has_ci のみ表示）
- L1を削除する場合、配下のL2を先に削除する必要あり（FKエラー防止）

## 将来対応（スコープ外）

- 重複の正当な理由分類（法規制・グループ会社・業務固有）
- scopeを判定ロジックに組み込む
- レベル3以降の階層追加
