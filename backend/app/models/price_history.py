from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ProductPriceHistory(Base):
    """PRODUCT_PRICE_HISTORY（商品単価変更履歴）。設計仕様書5.2節、出典DR-008。"""

    __tablename__ = "product_price_history"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_code: Mapped[str] = mapped_column(String(20), ForeignKey("products.product_code"), nullable=False, index=True)
    price_before: Mapped[int] = mapped_column(Integer, nullable=False)
    price_after: Mapped[int] = mapped_column(Integer, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
