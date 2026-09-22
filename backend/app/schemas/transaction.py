from datetime import datetime

from pydantic import BaseModel, Field


class TransactionItemRequest(BaseModel):
    product_code: str = Field(..., min_length=8, max_length=13)
    quantity: int = Field(..., ge=1, le=99)
    client_unit_price: int
    client_discount_amount: int = 0


class CreateTransactionRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=1, max_length=64)
    member_id: str | None = None
    # 明細数の上限は設計仕様書に記載がないため[AI提案・実装判断]。POSレジの現実的な1取引あたり品目数を踏まえた暫定値。
    items: list[TransactionItemRequest] = Field(..., min_length=1, max_length=200)
    client_subtotal: int
    client_total_incl_tax: int
    client_total_excl_tax: int


class TransactionItemResponse(BaseModel):
    product_code: str
    product_name_snapshot: str
    unit_price_snapshot: int
    quantity: int
    subtotal: int
    discount_id: int | None = None
    discount_amount_snapshot: int | None = None


class TransactionResponse(BaseModel):
    transaction_id: int
    transaction_datetime: datetime
    staff_id: str
    member_id: str | None = None
    total_amount_incl_tax: int
    total_amount_excl_tax: int
    tax_rate_applied: float
    items: list[TransactionItemResponse]
