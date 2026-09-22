from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TransactionItem(Base):
    """TRANSACTION_ITEMS（取引明細）。設計仕様書5.2節、出典DR-005・DR-008。単価・名称はスナップショット（BR-003）。"""

    __tablename__ = "transaction_items"

    transaction_item_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(String(20), ForeignKey("products.product_code"), nullable=False, index=True)
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_price_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("discounts.discount_id"), nullable=True)
    discount_amount_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default="0")
