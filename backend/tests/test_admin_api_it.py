"""IT-TAXCUR-*, IT-DISC-*, IT-TAXADMIN-*, IT-SEC-002〜003（FastAPIレベルの結合テスト）。"""
from datetime import date, timedelta

from tests.conftest import auth_headers


def test_it_taxcur_001_standard(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/tax-rates/current?tax_category=standard", headers=headers)
    assert res.status_code == 200
    assert res.json()["tax_category"] == "standard"


def test_it_taxcur_002_reduced(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/tax-rates/current?tax_category=reduced", headers=headers)
    assert res.status_code == 200
    assert res.json()["tax_category"] == "reduced"


def test_it_taxcur_003_invalid_category(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/tax-rates/current?tax_category=luxury", headers=headers)
    assert res.status_code == 400
    assert res.json()["error"]["type"] == "validation_error"


def test_it_disc_001_create_success(client, db_session):
    from app.models.product import Product

    db_session.add(Product(product_code="9999999999601", product_name="ITDISC商品", unit_price=1000, tax_category="standard"))
    db_session.commit()

    headers = auth_headers(client, "admin0012345", "AdminPass99")
    res = client.post(
        "/api/discounts",
        json={"product_code": "9999999999601", "discount_type": "rate", "discount_value": 10, "start_date": "2026-01-01", "end_date": "2026-01-31"},
        headers=headers,
    )
    assert res.status_code == 201
    assert res.json()["product_code"] == "9999999999601"


def test_it_disc_002_product_not_found(client):
    headers = auth_headers(client, "admin0012345", "AdminPass99")
    res = client.post(
        "/api/discounts",
        json={"product_code": "4909999999999", "discount_type": "rate", "discount_value": 10, "start_date": "2026-01-01", "end_date": "2026-01-31"},
        headers=headers,
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_it_disc_003_period_conflict(client, db_session):
    from app.models.discount import Discount
    from app.models.product import Product

    db_session.add(Product(product_code="9999999999602", product_name="ITDISC商品2", unit_price=1000, tax_category="standard"))
    db_session.flush()
    db_session.add(Discount(product_code="9999999999602", discount_type="rate", discount_value=10, start_date=date(2026, 3, 1), end_date=date(2026, 3, 31)))
    db_session.commit()

    headers = auth_headers(client, "admin0012345", "AdminPass99")
    res = client.post(
        "/api/discounts",
        json={"product_code": "9999999999602", "discount_type": "rate", "discount_value": 20, "start_date": "2026-03-15", "end_date": "2026-04-15"},
        headers=headers,
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "DISCOUNT_PERIOD_CONFLICT"


def test_it_disc_004_005_update_and_conflict(client, db_session):
    from app.models.discount import Discount
    from app.models.product import Product

    db_session.add(Product(product_code="9999999999603", product_name="ITDISC商品3", unit_price=1000, tax_category="standard"))
    db_session.flush()
    d1 = Discount(product_code="9999999999603", discount_type="rate", discount_value=10, start_date=date(2026, 5, 1), end_date=date(2026, 5, 31))
    d2 = Discount(product_code="9999999999603", discount_type="rate", discount_value=5, start_date=date(2026, 8, 1), end_date=date(2026, 8, 31))
    db_session.add(d1)
    db_session.add(d2)
    db_session.commit()
    d1_id = d1.discount_id
    d2_id = d2.discount_id

    headers = auth_headers(client, "admin0012345", "AdminPass99")

    # IT-DISC-004: 正常編集（重複しない期間へ変更）
    res = client.put(
        f"/api/discounts/{d1_id}",
        json={"product_code": "9999999999603", "discount_type": "rate", "discount_value": 15, "start_date": "2026-06-01", "end_date": "2026-06-30"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["discount_value"] == 15

    # IT-DISC-005: 編集後の期間がd2と重複
    res2 = client.put(
        f"/api/discounts/{d1_id}",
        json={"product_code": "9999999999603", "discount_type": "rate", "discount_value": 15, "start_date": "2026-08-15", "end_date": "2026-09-01"},
        headers=headers,
    )
    assert res2.status_code == 409


def test_it_disc_006_delete_removes_applicable_discount(client, db_session):
    from app.models.discount import Discount
    from app.models.product import Product

    db_session.add(Product(product_code="9999999999604", product_name="ITDISC商品4", unit_price=1000, tax_category="standard"))
    db_session.flush()
    today = date.today()
    d = Discount(product_code="9999999999604", discount_type="rate", discount_value=10, start_date=today - timedelta(days=1), end_date=today + timedelta(days=1))
    db_session.add(d)
    db_session.commit()
    discount_id = d.discount_id

    admin_headers = auth_headers(client, "admin0012345", "AdminPass99")
    staff_headers = auth_headers(client, "stf1", "Passw0rd")

    before = client.get("/api/products/9999999999604", headers=staff_headers)
    assert before.json()["applicable_discount"] is not None

    del_res = client.delete(f"/api/discounts/{discount_id}", headers=admin_headers)
    assert del_res.status_code == 204

    after = client.get("/api/products/9999999999604", headers=staff_headers)
    assert after.json()["applicable_discount"] is None


def test_it_disc_007_not_found_on_update_delete(client):
    headers = auth_headers(client, "admin0012345", "AdminPass99")
    res = client.put(
        "/api/discounts/99999999",
        json={"product_code": "49012345", "discount_type": "rate", "discount_value": 10, "start_date": "2026-01-01", "end_date": "2026-01-31"},
        headers=headers,
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "DISCOUNT_NOT_FOUND"

    res2 = client.delete("/api/discounts/99999999", headers=headers)
    assert res2.status_code == 404


def test_it_taxadmin_001_create_and_reflected_in_current(client):
    headers = auth_headers(client, "admin0012345", "AdminPass99")
    future_date = (date.today() + timedelta(days=1)).isoformat()
    res = client.post(
        "/api/tax-rates",
        json={"rate": 0.12, "tax_category": "standard", "effective_from": future_date},
        headers=headers,
    )
    assert res.status_code == 201

    current = client.get("/api/tax-rates/current?tax_category=standard", headers=headers)
    # 効力発生日はまだ来ていないため現行税率には反映されない（本日時点）
    assert current.json()["rate"] != 0.12


def test_it_taxadmin_002_list_returns_all(client):
    headers = auth_headers(client, "admin0012345", "AdminPass99")
    res = client.get("/api/tax-rates", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["tax_rates"]) >= 3


def test_ut_be_val_discamt_002_005_amount_upper_bound_vs_unit_price(client, db_session):
    """UT-BE-VAL-DISCAMT-002〜005: discount_type=amountは0円〜対象商品単価(1000円)未満が正常受理。"""
    from app.models.product import Product

    db_session.add(Product(product_code="9999999999501", product_name="DISCAMT境界確認用", unit_price=1000, tax_category="standard"))
    db_session.commit()

    headers = auth_headers(client, "admin0012345", "AdminPass99")

    def create(value, start, end):
        return client.post(
            "/api/discounts",
            json={"product_code": "9999999999501", "discount_type": "amount", "discount_value": value, "start_date": start, "end_date": end},
            headers=headers,
        )

    assert create(0, "2030-01-01", "2030-01-02").status_code == 201  # UT-BE-VAL-DISCAMT-002: 下限境界
    assert create(999, "2030-02-01", "2030-02-02").status_code == 201  # UT-BE-VAL-DISCAMT-003: 上限境界（単価未満）
    assert create(1000, "2030-03-01", "2030-03-02").status_code == 400  # UT-BE-VAL-DISCAMT-004: 上限+1（単価と同額）
    assert create(1001, "2030-04-01", "2030-04-02").status_code == 400  # UT-BE-VAL-DISCAMT-005: 単価超過


def test_it_sec_002_sql_injection_attempt_in_product_code(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.get("/api/products/' OR '1'='1", headers=headers)
    # パスパラメータの桁数・数字制約により400（バリデーションエラー）として弾かれる
    assert res.status_code in (400, 404, 422)
    assert "error" in res.json()


def test_it_sec_003_no_internal_details_leaked_on_validation_error(client):
    headers = auth_headers(client, "stf1", "Passw0rd")
    res = client.post("/api/transactions", json={"idempotency_key": "", "items": []}, headers=headers)
    body = res.text
    assert "Traceback" not in body
    assert "sqlalchemy" not in body.lower()
