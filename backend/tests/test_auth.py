"""UT-BE-AUTH-*, UT-BE-AUTH-ROLE-*, UT-BE-AUTH-LOCK-*（既存シードデータ TD-STAFF を使用）。
IT-AUTH-*, IT-ROLE-* と一部重複するAPIレベル結合検証を兼ねる。
"""
from datetime import datetime, timedelta, timezone

from app.models.staff import Staff
from tests.conftest import login


def test_ut_be_auth_001_login_success_staff_role(client):
    res = login(client, "stf1", "Passw0rd")
    assert res.status_code == 200
    body = res.json()
    assert body["staff_id"] == "stf1"
    assert body["staff_name"] == "山田一般"


def test_ut_be_auth_002_login_success_admin_role(client):
    res = login(client, "admin0012345", "AdminPass99")
    assert res.status_code == 200
    token = res.json()["access_token"]
    # role=adminであることをadmin限定APIへのアクセス成功で確認する
    admin_res = client.get("/api/discounts", headers={"Authorization": f"Bearer {token}"})
    assert admin_res.status_code == 200


def test_ut_be_auth_003_wrong_password(client):
    res = login(client, "stf1", "WrongPass1")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


def test_ut_be_auth_004_unknown_staff_id(client):
    res = login(client, "nouser9999", "Passw0rd")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


def test_ut_be_auth_005_failed_count_reset_on_success(client, db_session):
    # stf2はシード時点でfailed_login_count=4
    res = login(client, "stf2", "Passw0rd")
    assert res.status_code == 200
    staff = db_session.get(Staff, "stf2")
    assert staff.failed_login_count == 0


def test_ut_be_auth_role_002_staff_forbidden_on_admin_api(client):
    res = login(client, "stf1", "Passw0rd")
    token = res.json()["access_token"]
    res2 = client.get("/api/discounts", headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 403
    assert res2.json()["error"]["code"] == "ADMIN_ROLE_REQUIRED"


def test_ut_be_auth_lock_001_fourth_failure_then_success_not_locked(client):
    # stf2: failed_login_count=4（境界-1）。正しいパスワードでログインすればロックされず成功する。
    res = login(client, "stf2", "Passw0rd")
    assert res.status_code == 200


def test_ut_be_auth_lock_002_fifth_failure_locks_account(client, db_session):
    # stf2: failed_login_count=4の状態で誤ったパスワードを送ると5回目の失敗でロックされる
    res = login(client, "stf2", "WrongPass1")
    assert res.status_code == 401
    staff = db_session.get(Staff, "stf2")
    assert staff.failed_login_count == 5
    assert staff.locked_until is not None


def test_ut_be_auth_lock_003_locked_account_rejects_even_correct_password(client, db_session):
    # stf3のlocked_untilはシード投入時刻基準のため、実行時刻に対して再設定してから検証する
    # （seed_data.py実行からの経過時間に依存させないための対応）。
    staff = db_session.get(Staff, "stf3")
    staff.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
    db_session.commit()

    res = login(client, "stf3", "Passw0rd")
    assert res.status_code == 423
    assert res.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_ut_be_auth_lock_004_still_locked_boundary(client, db_session):
    # ロック解除1分前（境界値）の状態を再現し、まだロック中であることを確認する
    staff = db_session.get(Staff, "stf3")
    staff.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=1)
    db_session.commit()

    res = login(client, "stf3", "WrongPass1")
    assert res.status_code == 423


def test_ut_be_auth_lock_005_lock_expired_allows_login(client, db_session):
    # stf4: failed_login_count=5, locked_until=現在-1分（期限切れ）
    staff = db_session.get(Staff, "stf4")
    assert staff.locked_until.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    res = login(client, "stf4", "Passw0rd")
    assert res.status_code == 200
