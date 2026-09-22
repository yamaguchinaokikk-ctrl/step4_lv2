"""UT-BE-CALC-001〜012: Discount.calculateAmount 相当（app.services.discount_service.calculate_discount_amount）。"""
from decimal import Decimal

import pytest

from app.models.discount import Discount
from app.services.discount_service import calculate_discount_amount


def make_discount(discount_type: str, discount_value) -> Discount:
    return Discount(product_code="TEST", discount_type=discount_type, discount_value=Decimal(str(discount_value)))


@pytest.mark.parametrize(
    "test_id,discount_type,discount_value,unit_price,quantity,expected",
    [
        ("UT-BE-CALC-001", "rate", 10, 1000, 1, 100),
        ("UT-BE-CALC-002", "rate", 10, 1000, 99, 9900),
        ("UT-BE-CALC-003", "rate", 0, 1000, 1, 0),
        ("UT-BE-CALC-004", "rate", 100, 1000, 1, 1000),
        ("UT-BE-CALC-006", "rate", 50, 1000, 1, 500),
        ("UT-BE-CALC-007", "amount", 1, 1000, 1, 1),
        ("UT-BE-CALC-008", "amount", 0, 1000, 1, 0),
        ("UT-BE-CALC-009", "amount", 999, 1000, 1, 999),
        ("UT-BE-CALC-010", "amount", 999, 1000, 99, 98901),
    ],
)
def test_calculate_discount_amount(test_id, discount_type, discount_value, unit_price, quantity, expected):
    discount = make_discount(discount_type, discount_value)
    assert calculate_discount_amount(discount, unit_price, quantity) == expected, test_id


def test_ut_be_calc_005_rounding_behavior_documented():
    """UT-BE-CALC-005: 333×0.10=33.3、丸め方法は仕様上未定義（[要確認]）。
    実装はint()による切り捨てを採用している。この挙動を記録として固定する。"""
    discount = make_discount("rate", 10)
    result = calculate_discount_amount(discount, 333, 1)
    assert result == 33  # 実装は切り捨て（Decimal.to_integral_value既定はROUND_HALF_EVENだが33.3は33に丸まる）
