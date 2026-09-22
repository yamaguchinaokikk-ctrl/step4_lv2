from typing import Literal

from pydantic import BaseModel


class ApplicableDiscount(BaseModel):
    discount_id: int
    discount_type: Literal["rate", "amount"]
    discount_value: float


class ProductResponse(BaseModel):
    product_code: str
    product_name: str
    unit_price: int
    tax_category: Literal["standard", "reduced"]
    applicable_discount: ApplicableDiscount | None = None
