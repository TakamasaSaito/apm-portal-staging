# デマンド・プロジェクト管理機能 設計書

## 概要

IT投資申請（デマンド）を起票〜承認〜プロジェクト化まで一貫管理する機能。

## デマンドステージ

```
Draft → Submitted → Screening → Qualified → Approved → Completed
                                          ↓
                                       Rejected
```

| ステージ | 説明 |
|---------|------|
| Draft | 起票中（申請者が編集可能） |
| Submitted | 申請者が提出済み |
| Screening | 事務局が受付・一次審査中 |
| Qualified | 予備審査通過 |
| Approved | 承認済み |
| Rejected | 却下 |
| Completed | 完了 |

## 財務フィールド

ALTER TABLE で追加済み（既存DBとの互換性維持）：

| カラム | 型 | 説明 |
|--------|-----|------|
| score | INTEGER | 優先度スコア |
| investment_class | TEXT | 投資分類 |
| capital_expense | INTEGER | 設備投資額（万円） |
| operating_expense | INTEGER | 運用費（万円） |
| financial_benefit | INTEGER | 財務効果（万円） |
| npv | INTEGER | 正味現在価値 |
| roi_percent | REAL | ROI（%） |
| irr | REAL | 内部収益率 |
| discount_rate | REAL | 割引率 |
| capital_budget | INTEGER | 資本予算 |
| operating_budget | INTEGER | 運営予算 |
| demand_actual_cost | INTEGER | 実績コスト |

## プロジェクト自動生成

- stage=approved かつ project未作成時に「Create Project」ボタンを表示
- クリックで `POST /api/projects` を実行し `project` テーブルにレコード生成
- `demand_id` で紐付けを保持

## 画面タブ構成（デマンド詳細）

| タブ | 主な内容 |
|------|---------|
| Details | 基本情報（タイトル・カテゴリ・日程・担当者） |
| Business Case | ビジネス背景・期待効果・目的 |
| Financials | コスト計画テーブル（計画/実績・年度別） |
| Assessment Data | 財務指標（NPV・ROI・IRR）・スコア |
| Notes | フリーテキストメモ |
| Preferences | 優先度・リージョン・会社・BU設定 |

## Demand Workbench

バブルチャートでデマンドの優先度を可視化する画面。

- X軸：Risk
- Y軸：Value
- バブルサイズ：score
- 色：ステージ別
- バブルクリック：デマンド詳細画面へ遷移

API：`GET /api/dashboard/bubble`

## コスト計画（cost_plan）

| カラム | 説明 |
|--------|------|
| fiscal_year | 会計年度 |
| fiscal_period | 期（Q1〜Q4等） |
| cost_type | コスト種別（capital/operating等） |
| unit_cost | 単価 |
| quantity | 数量（デフォルト1） |
| planned_cost | 計画コスト |
| actual_cost | 実績コスト |

## プロジェクト（project）

| カラム | 説明 |
|--------|------|
| project_id | PK（UUID） |
| demand_id | 元となったデマンドID |
| title | プロジェクトタイトル |
| status | active / completed / cancelled |
| manager_user_id | PM |
| portfolio | ポートフォリオ区分 |
| description | 説明 |
