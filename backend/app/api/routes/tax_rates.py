from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff, get_db, require_admin
from app.core.errors import BusinessError
from app.models.tax_rate import TaxRate
from app.schemas.tax_rate import (
    TaxRateCreateRequest,
    TaxRateCurrentResponse,
    TaxRateListResponse,
    TaxRateResponse,
)
from app.services.tax_service import get_current_rate

router = APIRouter(tags=["tax-rates"])


@router.get("/api/tax-rates/current", response_model=TaxRateCurrentResponse)
def get_current_tax_rate(
    tax_category: Literal["standard", "reduced"] = Query(...),
    db: Session = Depends(get_db),
    current_staff=Depends(get_current_staff),
):
    """6.4.6節：現行消費税率の取得（FR-018）。"""
    tax_rate = get_current_rate(db, tax_category)
    if tax_rate is None:
        raise BusinessError(500, "SYSTEM_ERROR", "一時的なエラーが発生しました。しばらくしてから再度お試しください。")
    return TaxRateCurrentResponse(
        tax_category=tax_rate.tax_category,
        rate=float(tax_rate.rate),
        effective_from=tax_rate.effective_from,
    )


@router.get("/api/tax-rates", response_model=TaxRateListResponse)
def list_tax_rates(db: Session = Depends(get_db), current_staff=Depends(require_admin)):
    """6.4.15節：消費税率一覧取得（4章SC-04、管理者ロール限定）。"""
    rates = db.scalars(select(TaxRate).order_by(TaxRate.tax_category, TaxRate.effective_from)).all()
    return TaxRateListResponse(
        tax_rates=[
            TaxRateResponse(
                tax_rate_id=r.tax_rate_id,
                rate=float(r.rate),
                tax_category=r.tax_category,
                effective_from=r.effective_from,
            )
            for r in rates
        ]
    )


@router.post("/api/tax-rates", response_model=TaxRateResponse, status_code=status.HTTP_201_CREATED)
def create_tax_rate(
    payload: TaxRateCreateRequest,
    db: Session = Depends(get_db),
    current_staff=Depends(require_admin),
):
    """6.4.16節：消費税率の新規登録（4章SC-04、管理者ロール限定）。"""
    tax_rate = TaxRate(
        tax_category=payload.tax_category,
        rate=payload.rate,
        effective_from=payload.effective_from,
    )
    db.add(tax_rate)
    db.commit()
    db.refresh(tax_rate)
    return TaxRateResponse(
        tax_rate_id=tax_rate.tax_rate_id,
        rate=float(tax_rate.rate),
        tax_category=tax_rate.tax_category,
        effective_from=tax_rate.effective_from,
    )
