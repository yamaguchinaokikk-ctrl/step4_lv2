"""UT-BE-TXN-001〜009 / IT-TXN-001〜009（POST /api/transactions）。"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.models.discount import Discount
from app.models.product import Product
from tests.conftest import auth_headers


def new_key() -> str:
    return str(uuid.uuid4())


def base_body(idempotency_key, product_code="4901301234567", quantity=2, unit_price=1000, member_id=None, discount_amount=0):
    subtotal = unit_price * quantity - discount_amount
    return {
        "idempotency_key": idempotency_key,
        "member_id": member_id,
        "items": [
            {
                "product_code": product_code,
                "quantity": quantity,
                "client_unit_price": unit_price,
                "client_discount_amount": discount_amount,
            }
        ],
        "client_subtotal": subtotal,
        "client_total_incl_tax": round(subtotal * 1.10),
        "client_total_excl_tax": subtotal,
    }


def test_ut_be_txn_001_it_txn_001_server_recalc_match_and_saved(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    body = base_body(new_key())
    res = client.post("/api/transactions", json=body, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_amount_excl_tax"] == 2000
    assert data["total_amount_incl_tax"] == 2200
    assert data["member_id"] is None
    assert data["items"][0]["quantity"] == 2


def test_ut_be_txn_002_it_txn_004_amount_mismatch(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    body = base_body(new_key())
    body["client_total_incl_tax"] = 999999  # 意図的に不一致
    res = client.post("/api/transactions", json=body, headers=headers)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "AMOUNT_MISMATCH"


def test_ut_be_txn_003_no_member(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.post("/api/transactions", json=base_body(new_key(), member_id=None), headers=headers)
    assert res.status_code == 200
    assert res.json()["member_id"] is None


def test_ut_be_txn_004_member_not_found(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.post("/api/transactions", json=base_body(new_key(), member_id="M9999"), headers=headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "MEMBER_NOT_FOUND"


def test_ut_be_txn_005_product_not_found(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.post("/api/transactions", json=base_body(new_key(), product_code="4909999999999"), headers=headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_ut_be_txn_006_empty_items_rejected(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    body = base_body(new_key())
    body["items"] = []
    res = client.post("/api/transactions", json=body, headers=headers)
    assert res.status_code == 400


def test_ut_be_txn_007_008_idempotency_new_then_replay(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    key = new_key()
    body = base_body(key)
    res1 = client.post("/api/transactions", json=body, headers=headers)
    assert res1.status_code == 200
    txn_id_1 = res1.json()["transaction_id"]

    res2 = client.post("/api/transactions", json=body, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["transaction_id"] == txn_id_1  # 新規保存されず同一取引が返る


def test_ut_be_txn_009_it_txn_007_price_snapshot_preserved(client, db_session):
    headers = auth_headers(client, "stf1", "Passw0rd")
    product = Product(product_code="9999999999701", product_name="単価変更確認用", unit_price=1000, tax_category="standard")
    db_session.add(product)
    db_session.commit()

    body = base_body(new_key(), product_code="9999999999701", unit_price=1000)
    res = client.post("/api/transactions", json=body, headers=headers)
    assert res.status_code == 200
    assert res.json()["items"][0]["unit_price_snapshot"] == 1000

    # 確定後に商品マスタの単価を変更
    product.unit_price = 2000
    db_session.commit()

    # 既存取引明細のスナップショットは変化しない（レスポンスは再照会APIがないため同一トランザクション内DBを直接確認）
    from app.models.transaction_item import TransactionItem

    item = db_session.query(TransactionItem).filter(TransactionItem.product_code == "9999999999701").first()
    assert item.unit_price_snapshot == 1000


def test_it_txn_002_member_and_discount(client, db_session):
    headers = auth_headers(client, "stf1", "Passw0rd")
    product = Product(product_code="9999999999702", product_name="値引き対象2", unit_price=1000, tax_category="standard")
    db_session.add(product)
    db_session.flush()
    today = date.today()
    db_session.add(
        Discount(
            product_code="9999999999702",
            discount_type="amount",
            discount_value=Decimal("100"),
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=1),
        )
    )
    db_session.commit()

    body = base_body(new_key(), product_code="9999999999702", quantity=1, unit_price=1000, member_id="M001", discount_amount=100)
    res = client.post("/api/transactions", json=body, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["member_id"] == "M001"
    assert data["items"][0]["discount_amount_snapshot"] == 100
    assert data["items"][0]["subtotal"] == 900


def test_it_txn_003_mixed_tax_categories(client, db_session):
    headers = auth_headers(client, "stf1", "Passw0rd")
    key = new_key()
    # standard(4901301234567,1000) + reduced(4902345678901,300)
    body = {
        "idempotency_key": key,
        "member_id": None,
        "items": [
            {"product_code": "4901301234567", "quantity": 1, "client_unit_price": 1000, "client_discount_amount": 0},
            {"product_code": "4902345678901", "quantity": 1, "client_unit_price": 300, "client_discount_amount": 0},
        ],
        "client_subtotal": 1300,
        "client_total_incl_tax": 1000 + 100 + 300 + 24,  # standard10% + reduced8%
        "client_total_excl_tax": 1300,
    }
    res = client.post("/api/transactions", json=body, headers=headers)
    assert res.status_code == 200
    assert res.json()["total_amount_incl_tax"] == 1424


def test_it_txn_008_staff_id_not_taken_from_body(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    body = base_body(new_key())
    body["staff_id"] = "admin0012345"  # なりすまし試行（リクエストスキーマ上は無視される想定）
    res = client.post("/api/transactions", json=body, headers=headers)
    assert res.status_code == 200
    assert res.json()["staff_id"] == "stf1"  # JWTのsubが使われる
