from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Transaction(Base):
    """TRANSACTIONS（取引ヘッダ）。設計仕様書5.2節、出典DR-005。idempotency_keyはUNIQUE（二重送信対策、7.4.2(7)）。"""

    __tablename__ = "transactions"

    transaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    transaction_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    staff_id: Mapped[str] = mapped_column(String(20), ForeignKey("staff.staff_id"), nullable=False, index=True)
    member_id: Mapped[str | None] = mapped_column(String(20), ForeignKey("members.member_id"), nullable=True, index=True)
    total_amount_incl_tax: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount_excl_tax: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_rate_applied: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
