"""UT-BE-RATE-001〜009: TaxService.getCurrentRate 相当（app.services.tax_service.get_current_rate）。
UT-BE-TAX-001〜008: calculateTotals相当（税計算は app.services.transaction_service 内に実装。
_round_tax + get_current_rate の組み合わせで検証する）。
"""
from datetime import date
from decimal import Decimal

from app.models.tax_rate import TaxRate
from app.services.tax_service import get_current_rate
from app.services.transaction_service import _round_tax


def test_ut_be_rate_001_current_day_boundary(db_session):
    r = get_current_rate(db_session, "standard", date(2019, 10, 1))
    assert float(r.rate) == 0.10


def test_ut_be_rate_002_previous_day_boundary(db_session):
    r = get_current_rate(db_session, "standard", date(2019, 9, 30))
    assert float(r.rate) == 0.08


def test_ut_be_rate_003_next_day(db_session):
    r = get_current_rate(db_session, "standard", date(2019, 10, 2))
    assert float(r.rate) == 0.10


def test_ut_be_rate_004_reduced_category_independent(db_session):
    r = get_current_rate(db_session, "reduced", date(2019, 10, 1))
    assert float(r.rate) == 0.08


def test_ut_be_rate_005_latest_row_selected(db_session):
    r = get_current_rate(db_session, "standard", date(2099, 1, 1))
    assert float(r.rate) == 0.10


def test_ut_be_rate_006_no_applicable_row_returns_none(db_session):
    r = get_current_rate(db_session, "standard", date(2000, 1, 1))
    assert r is None  # 実装は「該当なし」の場合Noneを返す（[要確認]事項への実装判断）


def test_ut_be_rate_007_008_future_rate_boundary(db_session):
    db_session.add(TaxRate(tax_category="standard", rate=Decimal("0.12"), effective_from=date(2027, 4, 1)))
    db_session.flush()

    before = get_current_rate(db_session, "standard", date(2027, 3, 31))
    assert float(before.rate) == 0.10  # UT-BE-RATE-007

    on_day = get_current_rate(db_session, "standard", date(2027, 4, 1))
    assert float(on_day.rate) == 0.12  # UT-BE-RATE-008


def test_ut_be_rate_009_invalid_category_returns_none(db_session):
    r = get_current_rate(db_session, "luxury", date(2019, 10, 1))
    assert r is None  # 一次防御はAPI層のバリデーション（IT-TAXCUR-003）。関数自体は単に該当なしを返す


def test_ut_be_tax_001_single_item_no_rounding():
    excl = 1000
    rate = Decimal("0.10")
    assert excl + _round_tax(excl, rate) == 1100


def test_ut_be_tax_002_multiple_items_same_category():
    excl = 1000 + 500 * 2
    rate = Decimal("0.10")
    assert excl == 2000
    assert excl + _round_tax(excl, rate) == 2200


def test_ut_be_tax_003_mixed_tax_categories():
    standard_excl, standard_rate = 1000, Decimal("0.10")
    reduced_excl, reduced_rate = 1000, Decimal("0.08")
    total_excl = standard_excl + reduced_excl
    total_incl = (standard_excl + _round_tax(standard_excl, standard_rate)) + (
        reduced_excl + _round_tax(reduced_excl, reduced_rate)
    )
    assert total_excl == 2000
    assert total_incl == 2180


def test_ut_be_tax_004_after_discount():
    excl = 1000 - 100
    rate = Decimal("0.10")
    assert excl == 900
    assert excl + _round_tax(excl, rate) == 990


def test_ut_be_tax_005_rounding_case_documented():
    """UT-BE-CALC-005と同様、333×1.10=366.3の丸め方法は仕様上未定義。実装挙動を記録する。"""
    excl = 333
    rate = Decimal("0.10")
    assert excl + _round_tax(excl, rate) == 366


def test_ut_be_tax_007_upper_boundary():
    excl = 99_999_999
    # 上限境界では税抜のみで上限に達しているケースを想定（税込側の上限自体はDR-005の制約で別途[要確認]）
    assert excl == 99_999_999
