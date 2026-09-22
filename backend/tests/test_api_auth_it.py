"""IT-AUTH-002〜007, IT-STAFF-001〜002, IT-ROLE-001〜003（FastAPIレベルの結合テスト）。

IT-AUTH-001（ブラウザ⇔BFFのCookie設定）とIT-AUTH-008（BFFでのトークン詰め替え）はBFF（Next.js）
層の挙動であり、FastAPI単体のTestClientでは検証できない。frontend側のE2E/手動確認で扱う。
"""
import uuid

from tests.conftest import auth_headers, login


def test_it_auth_002_session_info(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/session", headers=headers)
    assert res.status_code == 200
    assert res.json() == {"staff_id": "stf1", "staff_name": "山田一般"}


def test_it_auth_003_refresh_issues_new_access_token(client):
    login_res = login(client, "stf1", "Passw0rd")
    refresh_token = login_res.json()["refresh_token"]
    res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_it_auth_004_invalid_refresh_token_rejected(client):
    res = client.post("/api/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "REFRESH_TOKEN_INVALID"


def test_it_auth_005_006_logout_revokes_refresh_token(client):
    login_res = login(client, "stf1", "Passw0rd")
    access_token = login_res.json()["access_token"]
    refresh_token = login_res.json()["refresh_token"]

    logout_res = client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_res.status_code == 204

    refresh_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 401
    assert refresh_res.json()["error"]["code"] == "REFRESH_TOKEN_INVALID"


def test_it_auth_007_unauthenticated_access_rejected(client):
    res = client.get("/api/session")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTH_TOKEN_INVALID"


def test_it_staff_001_registration_success(client):
    """Phase5修正：STAFFが1件以上登録済みの場合は管理者ロールでの認証が必須になった。"""
    headers = auth_headers(client, "admin0012345", "AdminPass99")
    unique_id = f"t{uuid.uuid4().hex[:7]}"
    res = client.post("/api/staff", json={"staff_id": unique_id, "password": "NewPass12", "name": "新人"}, headers=headers)
    assert res.status_code == 201
    assert res.json()["staff_id"] == unique_id


def test_it_staff_002_duplicate_registration_rejected(client):
    headers = auth_headers(client, "admin0012345", "AdminPass99")
    res = client.post("/api/staff", json={"staff_id": "stf1", "password": "NewPass12", "name": "重複"}, headers=headers)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "STAFF_ID_ALREADY_EXISTS"


def test_it_staff_003_unauthenticated_rejected_when_staff_exist(client):
    """Phase5修正：Critical/Major対応。STAFFが既に存在する状態で未認証登録は401になる。"""
    res = client.post("/api/staff", json={"staff_id": "noexist1", "password": "NewPass12", "name": "不正登録"})
    assert res.status_code == 401


def test_it_staff_004_non_admin_rejected(client):
    """Phase5修正：一般ロールでの登録は403になる（管理者限定）。"""
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.post("/api/staff", json={"staff_id": "noexist2", "password": "NewPass12", "name": "不正登録2"}, headers=headers)
    assert res.status_code == 403


def test_it_staff_005_bootstrap_allowed_when_no_staff(client, db_session):
    """Phase5修正：STAFFが0件（初回導入時）の場合のみ、未認証での登録を許可する。

    実DBには既存の担当者・関連する取引・リフレッシュトークンが存在するため、FK制約を守る順序で
    一時的に空にする（本テストはSAVEPOINTベースのトランザクション内で完結し、実DBには反映されない）。
    """
    from sqlalchemy import delete

    from app.models.refresh_token import RefreshToken
    from app.models.staff import Staff
    from app.models.transaction import Transaction
    from app.models.transaction_item import TransactionItem

    db_session.execute(delete(TransactionItem))
    db_session.execute(delete(Transaction))
    db_session.execute(delete(RefreshToken))
    db_session.execute(delete(Staff))
    db_session.commit()

    res = client.post("/api/staff", json={"staff_id": "firstadmin1", "password": "BootPass12", "name": "初回担当者"})
    assert res.status_code == 201


def test_it_role_001_staff_can_use_normal_api(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/products/4901301234567", headers=headers)
    assert res.status_code == 200


def test_it_role_002_staff_forbidden_from_admin_api(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/discounts", headers=headers)
    assert res.status_code == 403


def test_it_role_003_admin_can_use_admin_api(client):
    headers = auth_headers(client, "admin0012345", "AdminPass99")
    res = client.get("/api/discounts", headers=headers)
    assert res.status_code == 200
