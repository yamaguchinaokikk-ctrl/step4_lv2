from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_staff_optional, get_db
from app.core.errors import BusinessError
from app.core.security import hash_password
from app.models.staff import Staff
from app.schemas.staff import StaffCreateRequest, StaffCreateResponse

router = APIRouter(tags=["staff"])


@router.post("/api/staff", response_model=StaffCreateResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: StaffCreateRequest,
    db: Session = Depends(get_db),
    current_staff: CurrentStaff | None = Depends(get_current_staff_optional),
):
    """6.4.10節：担当者簡易登録（SC-03）。

    設計仕様書は「認証要否・権限チェックの詳細は詳細設計で検討する（[要確認]）」としており未確定。
    Phase5コードレビューでの指摘（第三者が誰でもstaffアカウントを作成できるアクセス制御の欠落）を受け、
    以下の方針とする（[AI提案・実装判断]。発注者確認事項として引き続き残る）：
    - STAFFテーブルが0件（初回導入時）の場合のみ、認証なしでの登録を許可する（ブートストラップ）
    - 1件以上登録済みの場合は、管理者ロール（admin）でのログインを必須とする
    """
    staff_count = db.scalar(select(func.count()).select_from(Staff))
    if staff_count > 0:
        if current_staff is None:
            raise BusinessError(401, "AUTH_TOKEN_INVALID", "認証が必要です")
        if current_staff.role != "admin":
            raise BusinessError(403, "ADMIN_ROLE_REQUIRED", "この操作には管理者権限が必要です")

    if db.get(Staff, payload.staff_id) is not None:
        raise BusinessError(409, "STAFF_ID_ALREADY_EXISTS", "指定した担当者IDは既に登録済みです")

    staff = Staff(
        staff_id=payload.staff_id,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role="staff",
    )
    db.add(staff)
    db.commit()

    return StaffCreateResponse(staff_id=staff.staff_id, staff_name=staff.name)
