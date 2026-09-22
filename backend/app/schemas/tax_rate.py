from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class TaxRateCurrentResponse(BaseModel):
    tax_category: Literal["standard", "reduced"]
    rate: float
    effective_from: date


class TaxRateResponse(BaseModel):
    tax_rate_id: int
    rate: float
    tax_category: Literal["standard", "reduced"]
    effective_from: date


class TaxRateListResponse(BaseModel):
    tax_rates: list[TaxRateResponse]


class TaxRateCreateRequest(BaseModel):
    rate: float = Field(..., ge=0, le=0.20)
    tax_category: Literal["standard", "reduced"]
    effective_from: date
