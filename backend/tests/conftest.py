import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_db
from app.db.session import engine
from app.main import app


@pytest.fixture()
def db_session():
    """テストごとにSAVEPOINTベースのトランザクションを開始し、終了時に外側トランザクションをロールバックする。

    アプリコード（例：ログインAPI）は内部でdb.commit()を呼ぶが、SAVEPOINTパターンにより
    その都度SAVEPOINTを切り直すことで、テスト終了時のtrans.rollback()で実DBへの永続化を防ぐ
    （SQLAlchemy公式の「外部トランザクションへのJoin」パターン）。
    """
    connection = engine.connect()
    trans = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = TestingSessionLocal()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def login(client: TestClient, staff_id: str, password: str):
    return client.post("/api/auth/login", json={"staff_id": staff_id, "password": password})


def auth_headers(client: TestClient, staff_id: str, password: str) -> dict:
    res = login(client, staff_id, password)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
