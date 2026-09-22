from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_staff, get_db
from app.core.errors import BusinessError
from app.models.staff import Staff
from app.schemas.auth import SessionResponse

router = APIRouter(tags=["session"])


@router.get("/api/session", response_model=SessionResponse)
def get_session(current_staff: CurrentStaff = Depends(get_current_staff), db: Session = Depends(get_db)):
    """6.4.9節：ログイン中の担当者情報を取得する（SCR-011表示用、[AI提案]）。"""
    staff = db.get(Staff, current_staff.staff_id)
    if staff is None:
        raise BusinessError(401, "AUTH_TOKEN_INVALID", "認証情報が無効です")
    return SessionResponse(staff_id=staff.staff_id, staff_name=staff.name)
