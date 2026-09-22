from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TaxRate(Base):
    """TAX_RATES（消費税率マスタ）。設計仕様書5.2節、出典DR-006。tax_category: standard/reduced。"""

    __tablename__ = "tax_rates"
    __table_args__ = (
        # 「現在有効な税率」選定クエリ（tax_category絞り込み＋effective_from降順）を高速化する複合索引。
        # Phase5コードレビュー指摘：Phase2計画時点では予定していたが実装時に単一列索引のみになっていた。
        Index("ix_tax_rates_category_effective_from", "tax_category", "effective_from"),
    )

    tax_rate_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tax_category: Mapped[str] = mapped_column(String(10), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
