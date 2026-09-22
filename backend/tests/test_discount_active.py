"""UT-BE-DISC-ACT-001〜005 / UT-BE-DISC-FIND-001〜004。

実装は`Discount.isActive()`を独立メソッドとして持たず、`find_applicable_discount()`のSQL条件
（start_date <= target_date <= end_date）に統合している（5.3節の役割分担はクラス設計レベルの
[AI提案]であり、実装時に見直される前提と明記されている）。そのため本テストはisActiveの境界値を
find_applicable_discountの有無判定を通じて検証する。
"""
from datetime import date
from decimal import Decimal

import pytest

from app.models.discount import Discount
from app.models.product import Product
from app.services.discount_service import find_applicable_discount

PRODUCT_CODE = "9999999999901"


@pytest.fixture()
def product_with_discount(db_session):
    product = Product(product_code=PRODUCT_CODE, product_name="テスト商品", unit_price=1000, tax_category="standard")
    db_session.add(product)
    db_session.flush()  # relationship()未定義のためFK依存の挿入順序を明示的に確定させる
    db_session.add(
        Discount(
            product_code=PRODUCT_CODE,
            discount_type="rate",
            discount_value=Decimal("10"),
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
        )
    )
    db_session.flush()
    return product


@pytest.mark.parametrize(
    "test_id,target_date,expect_active",
    [
        ("UT-BE-DISC-ACT-001", date(2026, 5, 31), False),
        ("UT-BE-DISC-ACT-002", date(2026, 6, 1), True),
        ("UT-BE-DISC-ACT-003", date(2026, 6, 15), True),
        ("UT-BE-DISC-ACT-004", date(2026, 6, 30), True),
        ("UT-BE-DISC-ACT-005", date(2026, 7, 1), False),
    ],
)
def test_isActive_boundary(db_session, product_with_discount, test_id, target_date, expect_active):
    result = find_applicable_discount(db_session, PRODUCT_CODE, target_date)
    assert (result is not None) == expect_active, test_id


def test_ut_be_disc_find_001_within_period(db_session, product_with_discount):
    result = find_applicable_discount(db_session, PRODUCT_CODE, date(2026, 6, 15))
    assert result is not None
    assert result.product_code == PRODUCT_CODE


def test_ut_be_disc_find_002_outside_period(db_session, product_with_discount):
    result = find_applicable_discount(db_session, PRODUCT_CODE, date(2026, 8, 1))
    assert result is None


def test_ut_be_disc_find_003_no_discount_record(db_session):
    product = Product(product_code="9999999999902", product_name="値引きなし商品", unit_price=500, tax_category="standard")
    db_session.add(product)
    db_session.flush()
    result = find_applicable_discount(db_session, "9999999999902", date(2026, 6, 15))
    assert result is None
