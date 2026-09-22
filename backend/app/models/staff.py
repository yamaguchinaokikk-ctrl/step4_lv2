from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Staff(Base):
    """STAFF（レジ担当者マスタ）。設計仕様書5.2節、出典DR-007。role: staff(一般)/admin(管理者)（BR-005）。"""

    __tablename__ = "staff"

    staff_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="staff")
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
