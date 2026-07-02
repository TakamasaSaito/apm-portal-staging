# SPMポータル 設計書インデックス

バージョン：1.0.0  
最終更新：2026-07-02  
リポジトリ：TakamasaSaito/apm-portal  

## 変更履歴
| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| 1.0.0 | 2026-07-02 | 初版作成 |

## ドキュメント構成
| ファイル | 内容 |
|---------|------|
| db.md | DBスキーマ・ERD |
| api.md | APIエンドポイント一覧 |
| workflows.md | ワークフロー・状態遷移図 |
| capability.md | Business Portfolio機能 |
| demand.md | デマンド・プロジェクト管理 |
| itsm.md | ITアセット管理 |
| scenario.md | シナリオナビゲーター |

## システム概要
- 名称：SPMポータル（ServiceNow SPM代替デモアプリ）
- 用途：EA Journey顧客向けシナリオ検証環境
- スタック：FastAPI + SQLite + Vanilla JS（single HTML）

## 環境
| 環境 | URL |
|------|-----|
| 本番 | https://web-production-d5d824.up.railway.app |
| ステージング | https://apm-portal-staging-production.up.railway.app |

## 開発運用ルール
- 機能追加・変更のたびに該当する設計書ファイルを更新する
- Claude Codeへの実装指示文の末尾に「docs/該当ファイルを更新する」を必ず含める
- Claude Code起動：`cd ~/apm-portal && git pull && claude --dangerously-skip-permissions`
