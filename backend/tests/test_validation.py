"""UT-BE-VAL-*: 設計仕様書6.2節の設定値定義に基づくバリデーション境界値テスト。"""
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest
from app.schemas.discount import DiscountCreateRequest
from app.schemas.staff import StaffCreateRequest
from app.schemas.tax_rate import TaxRateCreateRequest
from app.schemas.transaction import TransactionItemRequest


# 4.1 担当者ID（4〜12文字）
@pytest.mark.parametrize(
    "test_id,staff_id,should_pass",
    [
        ("UT-BE-VAL-STAFF-001", "abc", False),
        ("UT-BE-VAL-STAFF-002", "abcd", True),
        ("UT-BE-VAL-STAFF-003", "abcdefghijkl", True),
        ("UT-BE-VAL-STAFF-004", "abcdefghijklm", False),
    ],
)
def test_staff_id_length(test_id, staff_id, should_pass):
    kwargs = dict(staff_id=staff_id, password="Passw0rd")
    if should_pass:
        assert LoginRequest(**kwargs).staff_id == staff_id
    else:
        with pytest.raises(ValidationError):
            LoginRequest(**kwargs)


# 4.2 パスワード（8〜16文字、英数字両方） -- StaffCreateRequestで文字種検証まで実施
@pytest.mark.parametrize(
    "test_id,password,should_pass",
    [
        ("UT-BE-VAL-PASS-001", "Pass0rd", False),  # 7文字
        ("UT-BE-VAL-PASS-002", "Passw0rd", True),  # 8文字
        ("UT-BE-VAL-PASS-003", "Passw0rd12345678"[:16], True),  # 16文字
        ("UT-BE-VAL-PASS-004", "Passw0rd123456789", False),  # 17文字
        ("UT-BE-VAL-PASS-005", "abcdefghij", False),  # 英字のみ
        ("UT-BE-VAL-PASS-006", "1234567890", False),  # 数字のみ
    ],
)
def test_password_rules(test_id, password, should_pass):
    kwargs = dict(staff_id="stfx", password=password, name="テスト")
    if should_pass:
        assert StaffCreateRequest(**kwargs).password == password
    else:
        with pytest.raises(ValidationError):
            StaffCreateRequest(**kwargs)


def test_ut_be_val_pass_007_symbol_included_documented():
    """記号可否は仕様上未定義[要確認]。実装は英字・数字の存在のみ検証し、記号混入は許容する。"""
    req = StaffCreateRequest(staff_id="stfx", password="abc12345!", name="テスト")
    assert req.password == "abc12345!"


# 4.3 会員ID（4〜12文字）-- Path制約はAPI層のためここではmin/max_lengthの型として確認できないので
# schemas上に会員ID単体モデルはないため、API結合テスト（IT/後段）で境界確認する。UT観点は下記の桁数定義を明文化。
MEMBER_ID_MIN, MEMBER_ID_MAX = 4, 12


@pytest.mark.parametrize(
    "test_id,member_id,should_pass",
    [
        ("UT-BE-VAL-MEMBER-001", "M99", False),
        ("UT-BE-VAL-MEMBER-002", "M001", True),
        ("UT-BE-VAL-MEMBER-003", "M00000001234", True),
        ("UT-BE-VAL-MEMBER-004", "M000000012345", False),
    ],
)
def test_member_id_length_spec(test_id, member_id, should_pass):
    assert (MEMBER_ID_MIN <= len(member_id) <= MEMBER_ID_MAX) == should_pass


# 4.4 商品コード（8〜13桁）
@pytest.mark.parametrize(
    "test_id,product_code,should_pass",
    [
        ("UT-BE-VAL-PRODCODE-001", "4901234", False),
        ("UT-BE-VAL-PRODCODE-002", "49012345", True),
        ("UT-BE-VAL-PRODCODE-003", "4901301234567", True),
        ("UT-BE-VAL-PRODCODE-004", "49012345678901", False),
    ],
)
def test_product_code_length(test_id, product_code, should_pass):
    kwargs = dict(product_code=product_code, quantity=1, client_unit_price=1000)
    if should_pass:
        assert TransactionItemRequest(**kwargs).product_code == product_code
    else:
        with pytest.raises(ValidationError):
            TransactionItemRequest(**kwargs)


def test_ut_be_val_prodcode_005_non_numeric_documented():
    """英字混入時の扱いは仕様上未定義[要確認]。実装は桁数（文字数）のみ検証し文字種は制限しない。"""
    req = TransactionItemRequest(product_code="ABCDEFGH", quantity=1, client_unit_price=1000)
    assert req.product_code == "ABCDEFGH"


# 4.5 数量（1〜99）
@pytest.mark.parametrize(
    "test_id,quantity,should_pass",
    [
        ("UT-BE-VAL-QTY-001", 0, False),
        ("UT-BE-VAL-QTY-002", 1, True),
        ("UT-BE-VAL-QTY-003", 99, True),
    ],
)
def test_quantity_range(test_id, quantity, should_pass):
    kwargs = dict(product_code="49012345", quantity=quantity, client_unit_price=1000)
    if should_pass:
        assert TransactionItemRequest(**kwargs).quantity == quantity
    else:
        with pytest.raises(ValidationError):
            TransactionItemRequest(**kwargs)


def test_ut_be_val_qty_005_type_error():
    with pytest.raises(ValidationError):
        TransactionItemRequest(product_code="49012345", quantity="abc", client_unit_price=1000)


# 4.6 値引き率（rate、0〜100%）
@pytest.mark.parametrize(
    "test_id,value,should_pass",
    [
        ("UT-BE-VAL-DISCRATE-001", -1, False),
        ("UT-BE-VAL-DISCRATE-002", 0, True),
        ("UT-BE-VAL-DISCRATE-003", 100, True),
        ("UT-BE-VAL-DISCRATE-004", 101, False),
    ],
)
def test_discount_rate_range(test_id, value, should_pass):
    kwargs = dict(product_code="49012345", discount_type="rate", discount_value=value, start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
    if should_pass:
        assert DiscountCreateRequest(**kwargs).discount_value == value
    else:
        with pytest.raises(ValidationError):
            DiscountCreateRequest(**kwargs)


def test_ut_be_val_discamt_001_negative_rejected():
    with pytest.raises(ValidationError):
        DiscountCreateRequest(
            product_code="49012345", discount_type="amount", discount_value=-1,
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )


# 4.7 値引き額（amount、単価未満）は商品マスタ参照が必要なためAPI結合テスト（IT-DISC系）で検証する


# 4.8 消費税率（0〜20%）
@pytest.mark.parametrize(
    "test_id,rate,should_pass",
    [
        ("UT-BE-VAL-TAXRATE-001", -0.01, False),
        ("UT-BE-VAL-TAXRATE-002", 0.00, True),
        ("UT-BE-VAL-TAXRATE-003", 0.20, True),
        ("UT-BE-VAL-TAXRATE-004", 0.21, False),
    ],
)
def test_tax_rate_range(test_id, rate, should_pass):
    kwargs = dict(rate=rate, tax_category="standard", effective_from=date(2026, 1, 1))
    if should_pass:
        assert TaxRateCreateRequest(**kwargs).rate == rate
    else:
        with pytest.raises(ValidationError):
            TaxRateCreateRequest(**kwargs)
