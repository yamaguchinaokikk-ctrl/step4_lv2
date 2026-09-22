"""UT-BE-LOOKUP-PROD-*, UT-BE-LOOKUP-MEMBER-*（IT-PROD-*, IT-MEMBER-*を兼ねる）。"""
from tests.conftest import auth_headers


def test_ut_be_lookup_prod_001_found(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/products/4901301234567", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["product_code"] == "4901301234567"
    assert body["unit_price"] == 1000
    assert body["tax_category"] == "standard"


def test_ut_be_lookup_prod_002_not_found(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/products/4909999999999", headers=headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_ut_be_lookup_member_001_found(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/members/M001", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body == {"member_id": "M001", "member_name": "テスト太郎"}
    # 6.4.5節：電話番号・住所等は含まれない（データ最小化）
    assert "phone_number" not in body


def test_ut_be_lookup_member_002_not_found(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/members/M9999", headers=headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "MEMBER_NOT_FOUND"


def test_it_prod_001_product_with_active_discount(client, db_session):
    from datetime import date, timedelta
    from decimal import Decimal

    from app.models.discount import Discount
    from app.models.product import Product

    product = Product(product_code="9999999999801", product_name="値引き対象", unit_price=1000, tax_category="standard")
    db_session.add(product)
    db_session.flush()
    today = date.today()
    db_session.add(
        Discount(
            product_code="9999999999801",
            discount_type="rate",
            discount_value=Decimal("10"),
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=1),
        )
    )
    db_session.commit()

    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/products/9999999999801", headers=headers)
    assert res.status_code == 200
    assert res.json()["applicable_discount"] is not None
    assert res.json()["applicable_discount"]["discount_type"] == "rate"


def test_it_prod_002_product_without_discount(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/products/49012345", headers=headers)
    assert res.status_code == 200
    assert res.json()["applicable_discount"] is None
