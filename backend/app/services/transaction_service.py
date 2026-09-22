from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import BusinessError
from app.core.time import now_utc, to_db
from app.models.member import Member
from app.models.product import Product
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from app.schemas.transaction import CreateTransactionRequest, TransactionItemResponse, TransactionResponse
from app.services.discount_service import calculate_discount_amount, find_applicable_discount
from app.services.tax_service import get_current_rate


def _round_tax(excl_amount: int, rate: Decimal) -> int:
    return int((Decimal(excl_amount) * rate).to_integral_value(rounding=ROUND_HALF_UP))


def _build_response(transaction: Transaction, items: list[TransactionItem]) -> TransactionResponse:
    return TransactionResponse(
        transaction_id=transaction.transaction_id,
        transaction_datetime=transaction.transaction_datetime,
        staff_id=transaction.staff_id,
        member_id=transaction.member_id,
        total_amount_incl_tax=transaction.total_amount_incl_tax,
        total_amount_excl_tax=transaction.total_amount_excl_tax,
        tax_rate_applied=float(transaction.tax_rate_applied),
        items=[
            TransactionItemResponse(
                product_code=i.product_code,
                product_name_snapshot=i.product_name_snapshot,
                unit_price_snapshot=i.unit_price_snapshot,
                quantity=i.quantity,
                subtotal=i.subtotal,
                discount_id=i.discount_id,
                discount_amount_snapshot=i.discount_amount_snapshot,
            )
            for i in items
        ],
    )


def _existing_transaction(db: Session, idempotency_key: str) -> TransactionResponse | None:
    transaction = db.scalars(
        select(Transaction).where(Transaction.idempotency_key == idempotency_key)
    ).first()
    if transaction is None:
        return None
    items = db.scalars(
        select(TransactionItem).where(TransactionItem.transaction_id == transaction.transaction_id)
    ).all()
    return _build_response(transaction, list(items))


def confirm_purchase(db: Session, payload: CreateTransactionRequest, staff_id: str) -> TransactionResponse:
    """6.4.7節・7.4.2(3)(7)節：購入確定（金額二重検証＋冪等性）。"""

    # (7) 冪等性：既存のidempotency_keyがあれば新規計算・保存を行わず既存結果を返す
    existing = _existing_transaction(db, payload.idempotency_key)
    if existing is not None:
        return existing

    if payload.member_id is not None:
        member = db.get(Member, payload.member_id)
        if member is None:
            raise BusinessError(404, "MEMBER_NOT_FOUND", "会員IDが見つかりません")

    today = date.today()
    prepared_items: list[dict] = []
    excl_by_category: dict[str, int] = {}

    for line in payload.items:
        product = db.get(Product, line.product_code)
        if product is None:
            raise BusinessError(404, "PRODUCT_NOT_FOUND", f"商品がマスタ未登録です（{line.product_code}）")

        unit_price = product.unit_price
        discount_id = None
        discount_amount = 0

        # 値引き適用の要否（＝商品登録時点で会員IDが入力済みだったか）はフロントエンドの判断結果を尊重し、
        # サーバーは「値引き額が現在の値引きマスタと整合しているか」のみを検算する（7.4.2(3)節の補足）。
        # [AI提案・実装判断]：リクエストスキーマ（6.4.7節）に明細行ごとの適用要否フラグがないための解釈。
        if line.client_discount_amount and line.client_discount_amount > 0:
            discount = find_applicable_discount(db, line.product_code, today)
            if discount is not None:
                discount_id = discount.discount_id
                discount_amount = calculate_discount_amount(discount, unit_price, line.quantity)

        subtotal = unit_price * line.quantity - discount_amount

        prepared_items.append(
            {
                "product_code": product.product_code,
                "product_name_snapshot": product.product_name,
                "unit_price_snapshot": unit_price,
                "quantity": line.quantity,
                "subtotal": subtotal,
                "discount_id": discount_id,
                "discount_amount_snapshot": discount_amount,
                "tax_category": product.tax_category,
            }
        )
        excl_by_category[product.tax_category] = excl_by_category.get(product.tax_category, 0) + subtotal

    total_excl_tax = sum(item["subtotal"] for item in prepared_items)

    total_incl_tax = 0
    rate_by_category: dict[str, Decimal] = {}
    for tax_category, category_excl in excl_by_category.items():
        tax_rate = get_current_rate(db, tax_category, today)
        if tax_rate is None:
            raise BusinessError(500, "SYSTEM_ERROR", "一時的なエラーが発生しました。しばらくしてから再度お試しください。")
        rate_by_category[tax_category] = Decimal(tax_rate.rate)
        total_incl_tax += category_excl + _round_tax(category_excl, Decimal(tax_rate.rate))

    # TRANSACTIONS.tax_rate_applied は単一値のカラムのため、standardの税率を代表値として記録する。
    # 標準・軽減が混在する取引では代表値が実態と完全には一致しない（[要確認]、設計仕様書5.2節の制約）。
    representative_rate = rate_by_category.get("standard") or next(iter(rate_by_category.values()))

    if (
        total_excl_tax != payload.client_subtotal
        or total_excl_tax != payload.client_total_excl_tax
        or total_incl_tax != payload.client_total_incl_tax
    ):
        raise BusinessError(
            409,
            "AMOUNT_MISMATCH",
            "金額が一致しませんでした。もう一度商品をご確認のうえお試しください"
            "（商品の価格や値引き内容が変更された可能性があります）",
        )

    now = to_db(now_utc())
    transaction = Transaction(
        idempotency_key=payload.idempotency_key,
        transaction_datetime=now,
        staff_id=staff_id,
        member_id=payload.member_id,
        total_amount_incl_tax=total_incl_tax,
        total_amount_excl_tax=total_excl_tax,
        tax_rate_applied=representative_rate,
    )
    db.add(transaction)

    try:
        db.flush()
    except IntegrityError:
        # 同一idempotency_keyでのほぼ同時リクエスト（レースコンディション）。先着リクエストの結果を返す。
        db.rollback()
        existing = _existing_transaction(db, payload.idempotency_key)
        if existing is not None:
            return existing
        raise

    items: list[TransactionItem] = []
    for prepared in prepared_items:
        item = TransactionItem(
            transaction_id=transaction.transaction_id,
            product_code=prepared["product_code"],
            product_name_snapshot=prepared["product_name_snapshot"],
            unit_price_snapshot=prepared["unit_price_snapshot"],
            quantity=prepared["quantity"],
            subtotal=prepared["subtotal"],
            discount_id=prepared["discount_id"],
            discount_amount_snapshot=prepared["discount_amount_snapshot"],
        )
        db.add(item)
        items.append(item)

    db.commit()
    db.refresh(transaction)
    for item in items:
        db.refresh(item)

    return _build_response(transaction, items)
