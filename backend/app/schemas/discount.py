from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DiscountResponse(BaseModel):
    discount_id: int
    product_code: str
    discount_type: Literal["rate", "amount"]
    discount_value: float
    start_date: date
    end_date: date


class DiscountListResponse(BaseModel):
    discounts: list[DiscountResponse]


class DiscountCreateRequest(BaseModel):
    product_code: str = Field(..., min_length=8, max_length=13)
    discount_type: Literal["rate", "amount"]
    # rateは0〜100（%）、amountは0円以上（上限=対象商品単価未満はDB参照が必要なためサービス層で検証、6.2節）
    discount_value: float = Field(..., ge=0)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_range(self) -> "DiscountCreateRequest":
        if self.discount_type == "rate" and self.discount_value > 100:
            raise ValueError("値引き率（rate）は0〜100の範囲で指定してください")
        if self.end_date < self.start_date:
            raise ValueError("end_dateはstart_date以降の日付にしてください")
        return self
