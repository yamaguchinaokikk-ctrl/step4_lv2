from fastapi import APIRouter, Depends, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.core.errors import BusinessError, ValidationAppError
from app.models.discount import Discount
from app.models.product import Product
from app.schemas.discount import DiscountCreateRequest, DiscountListResponse, DiscountResponse
from app.services.discount_service import has_period_conflict

router = APIRouter(tags=["discounts"])


def _to_response(d: Discount) -> DiscountResponse:
    return DiscountResponse(
        discount_id=d.discount_id,
        product_code=d.product_code,
        discount_type=d.discount_type,
        discount_value=float(d.discount_value),
        start_date=d.start_date,
        end_date=d.end_date,
    )


def _validate_amount_upper_bound(payload: DiscountCreateRequest, product: Product) -> None:
    # 6.2節：discount_type=amountの上限は「対象商品の単価未満」
    if payload.discount_type == "amount" and payload.discount_value >= product.unit_price:
        raise ValidationAppError(
            "VALIDATION_ERROR",
            "値引き額（amount）は対象商品の単価未満で指定してください",
            {"field": "discount_value", "value": payload.discount_value, "unit_price": product.unit_price},
        )


@router.get("/api/discounts", response_model=DiscountListResponse)
def list_discounts(db: Session = Depends(get_db), current_staff=Depends(require_admin)):
    """6.4.11節：値引き一覧取得（4章SC-04、管理者ロール限定）。"""
    discounts = db.scalars(select(Discount).order_by(Discount.discount_id)).all()
    return DiscountListResponse(discounts=[_to_response(d) for d in discounts])


@router.post("/api/discounts", response_model=DiscountResponse, status_code=status.HTTP_201_CREATED)
def create_discount(
    payload: DiscountCreateRequest,
    db: Session = Depends(get_db),
    current_staff=Depends(require_admin),
):
    """6.4.12節：値引きの新規登録（4章SC-04、管理者ロール限定）。"""
    product = db.get(Product, payload.product_code)
    if product is None:
        raise BusinessError(404, "PRODUCT_NOT_FOUND", "商品がマスタ未登録です")

    _validate_amount_upper_bound(payload, product)

    if has_period_conflict(db, payload.product_code, payload.start_date, payload.end_date):
        raise BusinessError(409, "DISCOUNT_PERIOD_CONFLICT", "同一商品・重複期間の値引きが既に登録されています")

    discount = Discount(
        product_code=payload.product_code,
        discount_type=payload.discount_type,
        discount_value=payload.discount_value,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return _to_response(discount)


@router.put("/api/discounts/{discount_id}", response_model=DiscountResponse)
def update_discount(
    payload: DiscountCreateRequest,
    discount_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_staff=Depends(require_admin),
):
    """6.4.13節：値引きの編集（管理者ロール限定）。"""
    discount = db.get(Discount, discount_id)
    if discount is None:
        raise BusinessError(404, "DISCOUNT_NOT_FOUND", "指定した値引きが見つかりません")

    product = db.get(Product, payload.product_code)
    if product is None:
        raise BusinessError(404, "PRODUCT_NOT_FOUND", "商品がマスタ未登録です")

    _validate_amount_upper_bound(payload, product)

    if has_period_conflict(db, payload.product_code, payload.start_date, payload.end_date, exclude_discount_id=discount_id):
        raise BusinessError(409, "DISCOUNT_PERIOD_CONFLICT", "同一商品・重複期間の値引きが既に登録されています")

    discount.product_code = payload.product_code
    discount.discount_type = payload.discount_type
    discount.discount_value = payload.discount_value
    discount.start_date = payload.start_date
    discount.end_date = payload.end_date
    db.commit()
    db.refresh(discount)
    return _to_response(discount)


@router.delete("/api/discounts/{discount_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_discount(
    discount_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_staff=Depends(require_admin),
):
    """6.4.14節：値引きの削除（管理者ロール限定）。"""
    discount = db.get(Discount, discount_id)
    if discount is None:
        raise BusinessError(404, "DISCOUNT_NOT_FOUND", "指定した値引きが見つかりません")
    db.delete(discount)
    db.commit()
    return None
