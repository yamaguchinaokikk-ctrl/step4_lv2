from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api.deps import get_current_staff, get_db
from app.core.errors import BusinessError
from app.models.member import Member
from app.schemas.member import MemberResponse

router = APIRouter(tags=["members"])


@router.get("/api/members/{member_id}", response_model=MemberResponse)
def get_member(
    member_id: str = Path(..., min_length=4, max_length=12),
    db: Session = Depends(get_db),
    current_staff=Depends(get_current_staff),
):
    """6.4.5節：会員照会（FR-014）。存在しない場合は404で入力を拒否する（ISS-008解消）。"""
    member = db.get(Member, member_id)
    if member is None:
        raise BusinessError(404, "MEMBER_NOT_FOUND", "会員IDが見つかりません")
    return MemberResponse(member_id=member.member_id, member_name=member.name)
