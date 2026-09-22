"""設計仕様書6.3節：エラー処理方針の共通実装。

エラー分類: validation_error(400) / business_error(401/403/404/409/423) / system_error(500)
レスポンス形式: {"error": {"type", "code", "message", "details"}}
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app")


class AppError(Exception):
    """業務エラー・バリデーションエラーの基底クラス。"""

    def __init__(self, status_code: int, error_type: str, code: str, message: str, details: dict | None = None):
        self.status_code = status_code
        self.error_type = error_type
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class ValidationAppError(AppError):
    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(status.HTTP_400_BAD_REQUEST, "validation_error", code, message, details)


class BusinessError(AppError):
    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        super().__init__(status_code, "business_error", code, message, details)


def _error_body(error_type: str, code: str, message: str, details: dict | None) -> dict:
    return {"error": {"type": error_type, "code": code, "message": message, "details": details}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.error_type, exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_error_body(
                "validation_error",
                "VALIDATION_ERROR",
                "入力内容を確認してください",
                {"errors": exc.errors()},
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        # システムエラー時はスタックトレース等の内部詳細を一切開示しない（6.3節）。詳細はログにのみ記録する。
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                "system_error",
                "SYSTEM_ERROR",
                "一時的なエラーが発生しました。しばらくしてから再度お試しください。",
                None,
            ),
        )
