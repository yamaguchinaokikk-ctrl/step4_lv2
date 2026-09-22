from pydantic import BaseModel


class MemberResponse(BaseModel):
    # 6.4.5節：MEMBERSには電話番号・住所・性別・年齢もあるが、SCR-012の表示要件にないため最小権限でレスポンスに含めない
    member_id: str
    member_name: str
