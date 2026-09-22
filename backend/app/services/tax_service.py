from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tax_rate import TaxRate


def get_current_rate(db: Session, tax_category: str, target_date: date | None = None) -> TaxRate | None:
    """現在有効な税率を取得する（設計仕様書5.2節TAX_RATES節）。

    選定ロジック（[AI提案]）：同一tax_categoryの中で、effective_fromがtarget_date以前の行のうち、
    effective_fromが最も新しい1件。
    """
    target_date = target_date or date.today()
    stmt = (
        select(TaxRate)
        .where(TaxRate.tax_category == tax_category, TaxRate.effective_from <= target_date)
        .order_by(TaxRate.effective_from.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()
