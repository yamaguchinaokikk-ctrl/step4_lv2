from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discount import Discount


def find_applicable_discount(db: Session, product_code: str, target_date: date | None = None) -> Discount | None:
    """現在有効な値引きを取得する（1商品1値引き、ISS-007）。設計仕様書5.2節DISCOUNTS。"""
    target_date = target_date or date.today()
    stmt = select(Discount).where(
        Discount.product_code == product_code,
        Discount.start_date <= target_date,
        Discount.end_date >= target_date,
    )
    return db.scalars(stmt).first()


def calculate_discount_amount(discount: Discount, unit_price: int, quantity: int) -> int:
    """明細行の値引き合計額を算出する（設計仕様書5.3節 Discount.calculateAmount()）。

    discount_type='amount': 商品1個あたりの値引き額 × quantity
    discount_type='rate': unit_price × quantity × (discount_value / 100)
    """
    if discount.discount_type == "amount":
        return int(discount.discount_value) * quantity
    rate = Decimal(discount.discount_value) / Decimal(100)
    return int((Decimal(unit_price) * quantity * rate).to_integral_value())


def has_period_conflict(
    db: Session,
    product_code: str,
    start_date: date,
    end_date: date,
    exclude_discount_id: int | None = None,
) -> bool:
    """同一product_codeで有効期間が重複する値引きが既に登録されているか（1商品1値引き制約、5章）。"""
    stmt = select(Discount).where(
        Discount.product_code == product_code,
        Discount.start_date <= end_date,
        Discount.end_date >= start_date,
    )
    if exclude_discount_id is not None:
        stmt = stmt.where(Discount.discount_id != exclude_discount_id)
    return db.scalars(stmt).first() is not None
