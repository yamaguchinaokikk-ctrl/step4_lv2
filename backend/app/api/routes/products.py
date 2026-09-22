from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff, get_db
from app.core.errors import BusinessError
from app.models.product import Product
from app.schemas.product import ApplicableDiscount, ProductResponse
from app.services.discount_service import find_applicable_discount

router = APIRouter(tags=["products"])


@router.get("/api/products/{product_code}", response_model=ProductResponse)
def get_product(
    product_code: str = Path(..., min_length=8, max_length=13, pattern=r"^\d+$"),
    db: Session = Depends(get_db),
    current_staff=Depends(get_current_staff),
):
    """6.4.4節：商品マスタ照合（FR-022, FR-023）。バーコードスキャン・手入力共通。"""
    product = db.get(Product, product_code)
    if product is None:
        raise BusinessError(404, "PRODUCT_NOT_FOUND", "商品がマスタ未登録です")

    discount = find_applicable_discount(db, product_code)
    applicable_discount = None
    if discount is not None:
        applicable_discount = ApplicableDiscount(
            discount_id=discount.discount_id,
            discount_type=discount.discount_type,
            discount_value=float(discount.discount_value),
        )

    return ProductResponse(
        product_code=product.product_code,
        product_name=product.product_name,
        unit_price=product.unit_price,
        tax_category=product.tax_category,
        applicable_discount=applicable_discount,
    )
