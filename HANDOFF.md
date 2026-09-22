# HANDOFF.md — 実装引き継ぎメモ

AI駆動開発（Phase1調査〜Phase6マージ準備）で実装した簡易POSアプリ（Lv1+Lv2）の引き継ぎ情報。
仕様の正式な記録は `07_要件定義書.md` / `設計仕様書.md` / `テスト仕様書/` を正とする。本ファイルは
それらに書ききれない「今から着手する人向けの実務メモ」。

## 経緯（AI駆動開発 Phase1〜6の記録）

2026-09-22〜23、Claude Codeを用いたAI駆動開発（専門家レビュー方式）で、設計仕様書・テスト仕様書
（本リポジトリに既存だった`07_要件定義書.md`・`設計仕様書.md`・`テスト仕様書/`）を最優先の根拠として、
以下の6フェーズで実装からGitHub公開までを一気通貫で行った。各フェーズはユーザーの明示的な指示で開始し、
Phase間の引き継ぎはコンテキスト（会話）で行った。

### Phase 1：調査
リポジトリには仕様書一式のみでコード資産がないことを確認。要件定義書のID体系（BR/FR/SCR/DR/IF/NFR/
CON/ASM）、設計仕様書の`[AI提案]`/`[要確認]`タグの意味、テスト仕様書の構成（UT118/IT45/E2E38/UAT24件）
を把握した。

### Phase 2：仕様分析・実装計画
DB未確定だったTBD-001（バックエンドホスティング）・ISS-016（パスワードハッシュ方式）をユーザーに確認し、
以下を確定：DB＝Azure MySQL Flexible Server（`gen12-mysql-pos`）に新規スキーマ`pod_Gussan`を作成、
パスワードハッシュ＝bcrypt、バックエンドホスティング＝Azure App Service、リポジトリ構成＝モノレポ。
設計仕様書6.1/6.4.8節に矛盾がある`GET /api/transactions/{id}`（対象外と明記されているのにAPI仕様が
フル記載されている）を発見し、実装対象外として扱う方針をユーザーに確認した。

### Phase 3：実装・DB構築
FastAPI（バックエンド）・Next.js（フロントエンド、BFF構成）を実装。Azure MySQLへの接続がファイアウォール
未許可でタイムアウトしたため、Azure CLIでの許可ルール追加についてユーザー承認を得たうえで対応（CLIの
認証トークンが失効していたためデバイスコード認証をユーザーに依頼）。`pod_Gussan`スキーマを作成し、
Alembicで9テーブルをマイグレーション。DBパスワードに含まれる`@`記号がSQLAlchemy接続URLの区切り文字と
衝突するバグに気づき、URLエンコードで修正。実サーバーでのエンドツーエンド動作確認を実施した。

### Phase 4：テスト
テスト仕様書の実際のTest ID（UT-BE-CALC-*等）に対応させる形でバックエンドpytest・フロントエンドJest・
Playwright E2Eを実装し、実DBに対して実行。実行中に以下を発見・修正：
- シードデータのロックアウト時刻がセッション経過時間により実行時点で無効化されていた（テスト環境の問題）
- E2Eテストの`loginAs`ヘルパーが、ログイン後のURL遷移を待たずに次の操作へ進んでしまうバグ（テストコードの
  実装ミス）
- `AdminDiscounts.tsx`（SC-04）の`<label>`が`htmlFor`で関連付けられておらず、E2Eから要素を特定できな
  かった（アプリ本体の軽微な実装ミス、修正済み）

最終的にバックエンド117件・フロントエンド8件・E2E 20シナリオが全PASS。UATは性質上未実施とした。

### Phase 5：コードレビュー
第三者シニアエンジニアの視点で実コードを精査し、Critical 0件・Major 5件・Minor 6件を検出。特に
`POST /api/staff`が完全に認証不要だった点（第三者が誰でもレジ業務用アカウントを作成できる）を最も
重大なMajorとして是正し、STAFFが0件のときのみ許可するブートストラップ方式＋以降は管理者ロール必須に
変更した。`TAX_RATES`への複合インデックス追加作業中、モデルの`__tablename__`（大文字）と実DB上の
テーブル名（`lower_case_table_names=1`により小文字）の不一致により、`alembic revision --autogenerate`
が全テーブルをDROP/CREATEしようとする危険な差分を生成することを発見。**この危険なマイグレーションは
未適用のまま破棄**し、全モデルの`__tablename__`とFK参照を実DBの命名（小文字）へ是正したうえで、
複合インデックス追加のみの安全なマイグレーションを作成・適用した。修正後、バックエンド120件・E2E 21件
（Major対応に伴うテスト更新・追加を含む）で再度全PASSを確認。

### Phase 6：Git・GitHubへのマージ
Publicリポジトリ公開前のセキュリティ確認として、ステージ対象の全ファイルに対し実際のパスワード・JWT
シークレット・DBホスト名・共有ユーザー名（`tech0`）が含まれていないことをgrepで確認。その過程で
`backend/.env.example`に実際のDBホスト名・共有ユーザー名が残っていたことに気づき、汎用プレースホルダーに
修正した。Playwrightのテスト成果物等、コミット不要なファイルも`.gitignore`に追加。実装一式（107
ファイル）をコミットしたのち、`origin/main`（Public）への`git push`はユーザーに最終確認を取ってから
実行した。

### 主な技術的な学び（今後同様の構成で開発する際の参考）
- MySQL（`lower_case_table_names=1`）環境でSQLAlchemyモデルを書く場合、`__tablename__`は最初から
  実DBの命名規則（小文字）に合わせておかないと、Alembicの自動生成マイグレーションが誤作動する
- DBパスワードに`@`等のURL予約文字が含まれる場合は`urllib.parse.quote_plus`でエンコードする
- pytestで実DBを使う結合テストは、SQLAlchemyの「外部トランザクションへのJoin（SAVEPOINT）」パターンで
  ラップすると、アプリコード内の`db.commit()`呼び出しに関わらず安全にロールバックできる
- Playwrightの`waitForURL`に「遷移前の現在値も満たしてしまう正規表現」を渡すと、実際のナビゲーションを
  待たずに即座に解決してしまう（並列実行時のみ顕在化しやすく気づきにくい）

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
