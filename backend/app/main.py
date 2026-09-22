from fastapi import FastAPI

from app.api.routes import all_routers
from app.core.config import settings
from app.core.errors import register_exception_handlers

# 7.4.2(4)節：本番環境ではSwagger/OpenAPI Docsを非公開にする
docs_kwargs = (
    {"docs_url": None, "redoc_url": None, "openapi_url": None}
    if settings.is_production
    else {}
)

app = FastAPI(title="簡易POSアプリ API", version="1.0.0", **docs_kwargs)

register_exception_handlers(app)

for router in all_routers:
    app.include_router(router)


@app.get("/healthz", tags=["health"])
def healthz():
    return {"status": "ok"}
