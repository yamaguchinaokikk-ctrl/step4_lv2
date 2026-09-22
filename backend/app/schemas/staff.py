import re

from pydantic import BaseModel, Field, field_validator


class StaffCreateRequest(BaseModel):
    staff_id: str = Field(..., min_length=4, max_length=12)
    password: str = Field(..., min_length=8, max_length=16)
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def password_must_contain_letters_and_digits(cls, v: str) -> str:
        # 6.2節：パスワードは英字・数字の両方を含む（[AI提案]）
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("パスワードは英字・数字の両方を含めてください")
        return v


class StaffCreateResponse(BaseModel):
    staff_id: str
    staff_name: str
