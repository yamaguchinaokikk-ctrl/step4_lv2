from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Discount(Base):
    """DISCOUNTS（値引きマスタ）。設計仕様書5.2節、出典DR-003。1商品1値引き（ISS-007）。"""

    __tablename__ = "discounts"

    discount_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_code: Mapped[str] = mapped_column(String(20), ForeignKey("products.product_code"), nullable=False, index=True)
    discount_type: Mapped[str] = mapped_column(Enum("rate", "amount", name="discount_type_enum"), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
