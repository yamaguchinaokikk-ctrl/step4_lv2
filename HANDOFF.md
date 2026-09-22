# HANDOFF.md — 実装引き継ぎメモ

AI駆動開発（Phase1調査〜Phase6マージ準備）で実装した簡易POSアプリ（Lv1+Lv2）の引き継ぎ情報。
仕様の正式な記録は `07_要件定義書.md` / `設計仕様書.md` / `テスト仕様書/` を正とする。本ファイルは
それらに書ききれない「今から着手する人向けの実務メモ」。

## セットアップ

### バックエンド（FastAPI）

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env    # DB接続情報・JWTシークレットを実際の値に書き換える
alembic upgrade head    # pod_Gussanスキーマに9テーブルを作成
python -m seed.seed_data  # テストデータ設計書準拠のシードデータ投入（任意）
uvicorn app.main:app --reload
```

`.env` はGit管理対象外（`.gitignore`済み）。DBパスワード・JWTシークレットは各自で用意すること。

### フロントエンド（Next.js）

```bash
cd frontend
npm install
cp .env.example .env.local  # BACKEND_API_BASE_URL（通常はhttp://localhost:8000のままでよい）
npm run dev
```

### テスト

```bash
# バックエンド（実DBに対して実行。SAVEPOINTで自動ロールバックされるため実データは汚染しない）
cd backend && python -m pytest tests/ -v

# フロントエンド単体テスト
cd frontend && npm test

# E2E（backend・frontendの両devサーバーを起動した状態で実行）
cd frontend && npx playwright install chromium  # 初回のみ
npx playwright test
```

## DB

- Azure Database for MySQL Flexible Server（既存の共有サーバー）に新規スキーマ `pod_Gussan` を作成して使用している。同一サーバー上の他スキーマ（他受講生のもの）には触れていない。
- マイグレーションは `backend/alembic/versions/` で管理。`alembic upgrade head` で追随できる。
- 本サーバーは `lower_case_table_names=1` のため、SQLAlchemyモデルの `__tablename__` は小文字で統一している（大文字にすると `alembic revision --autogenerate` が誤って全テーブルを削除・再作成しようとする、Phase5で発見）。

## 未対応事項（[要確認] のまま残っているもの）

- パスワードロックアウトの具体的な回数・時間（5回/15分）は設計仕様書上も暫定値のまま
- バーコードスキャン失敗時の挙動（ISS-009）
- `TRANSACTIONS.tax_rate_applied` は単一カラムのため、標準・軽減税率混在取引では代表値（standard優先）しか記録できない（金額自体は明細ごとに正しく計算・保存される）
- CSP（Content-Security-Policy）ヘッダー未導入（カメラ機能を壊すリスクがあるため見送り。基本的なセキュリティヘッダーのみ導入済み）
- ログインのブルートフォース対策はアカウント単位のロックアウトのみ（IP単位のレート制限なし）
- `PosMain.tsx` が複数責務を持つ大きめのコンポーネント（327行）。将来的な分割を推奨
- `GET /api/transactions/{id}` は設計仕様書の指示により未実装（詳細は設計仕様書6.4.8節）

## 注意事項

- `POST /api/staff`（担当者簡易登録）は、STAFFが0件（初回導入時）の場合のみ認証不要。1件でも登録済みなら管理者ロール必須（Phase5でアクセス制御の不備を修正）
- E2Eテスト（Playwright）は実DBに対して実行するため、管理者用の値引き・税率登録テスト等でテストデータが残ることがある。定期的に不要データを削除すること
- ローカル開発でAzure MySQLに接続できない場合、Azure Portal側のファイアウォール規則に開発機のIPが登録されているか確認すること
