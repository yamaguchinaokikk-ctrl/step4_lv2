from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_staff, get_db
from app.schemas.transaction import CreateTransactionRequest, TransactionResponse
from app.services.transaction_service import confirm_purchase

router = APIRouter(tags=["transactions"])

# 注記：GET /api/transactions/{transaction_id}（設計仕様書6.1節No.8・6.4.8節）は、
# 設計仕様書内で「現時点では設計・実装の対象としない」と明記されているため実装しない（Phase 2整合性確認済み）。


@router.post("/api/transactions", response_model=TransactionResponse)
def create_transaction(
    payload: CreateTransactionRequest,
    db: Session = Depends(get_db),
    current_staff: CurrentStaff = Depends(get_current_staff),
):
    """6.4.7節：購入確定。staff_idはリクエストボディではなくJWTのsubから取得する。"""
    return confirm_purchase(db, payload, current_staff.staff_id)
