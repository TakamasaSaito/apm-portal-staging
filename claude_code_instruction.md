# APMポータル DB連携実装の依頼

## 背景
添付の `apm_portal.html` は、ビジネスアプリケーション（システム）管理と、その新規登録・更新・廃止申請の承認ワークフローを実装したフロントエンドのプロトタイプです。現状、データはJavaScriptの配列にハードコードされています。

このプロトタイプのUI・操作感を維持したまま、SQLiteデータベースと連携させ、データが永続化される形に作り替えてください。

## データベース設計（ER図参照: er_diagram.mermaid）

以下5テーブルでSQLiteデータベースを構築してください。

### department（部署マスター）
- department_id (PK, 自動採番)
- department_name

### user（ユーザマスター）
- user_id (PK, 自動採番)
- user_name
- department_id (FK -> department)
- role

### application（ビジネスアプリケーション/システムマスター）
- application_id (PK, 文字列, 例: APM-001)
- application_name
- owner_department_id (FK -> department)
- status（running/plan/dev/order/retire）
- vendor
- business_owner
- system_owner
- ops_manager
- dev_manager
- start_plan, start_actual, end_plan, end_actual（日付、未定の場合はNULL）

### environment（システム環境マスター）
- environment_id (PK, 自動採番)
- application_id (FK -> application)
- env_type（本番環境/ステージング環境/開発環境/テスト環境）
- location, ip, host, os, middleware, cpu_mem, storage

### apm_request（APM申請：新規登録/更新/廃止）
- request_id (PK, 文字列, 例: REQ-001)
- type（register/update/retire）
- application_id (FK -> application、新規登録の場合はNULL可)
- applicant_user_id (FK -> user)
- applied_at（日時）
- status（pending/approved/rejected）
- approver_user_id (FK -> user, NULL可)
- approved_at（日時、NULL可）
- reason
- changes（JSON文字列。更新申請時の変更前後の差分を格納）
- 新規登録申請用の追加項目: dept, biz_owner, new_status, start_plan
- 廃止申請用の追加項目: end_plan

## 実装方針

1. SQLiteのDBファイルを作成し、上記スキーマでテーブルを作成するスクリプトを用意してください。
2. 添付HTMLのサンプルデータ（apps配列、envs配列、requests配列）を初期データとして投入してください。ただし、ユーザー名（"田中 部長"等）はuserテーブルに正規化し、department（"人事部"等）もdepartmentテーブルに正規化してください。
3. バックエンドは適切な軽量フレームワーク（Python/FastAPIまたはNode/Express等、提案歓迎）でAPIサーバーを構築し、以下の操作をDBに対して行えるようにしてください。
   - アプリケーション一覧の取得・検索・フィルタ
   - アプリケーション詳細の取得
   - 環境情報の追加・更新・削除（即時反映）
   - 申請（新規登録/更新/廃止）の作成
   - 申請履歴の取得
   - 承認・却下処理（承認時、retireタイプならapplicationのstatusとend_actualを更新）
4. フロントエンド（HTML/JS）は既存の見た目・操作感を維持しつつ、ハードコードされた配列操作をAPI呼び出しに置き換えてください。
5. CSV出力機能は維持してください（DBから取得したデータを出力）。

## 確認したいこと
実装を始める前に、フレームワーク選定（言語・フレームワーク）と全体のディレクトリ構成案を提示してください。承認後に実装を進めてください。
