from app.api.routes.auth import router as auth_router
from app.api.routes.discounts import router as discounts_router
from app.api.routes.members import router as members_router
from app.api.routes.products import router as products_router
from app.api.routes.session import router as session_router
from app.api.routes.staff import router as staff_router
from app.api.routes.tax_rates import router as tax_rates_router
from app.api.routes.transactions import router as transactions_router

all_routers = [
    auth_router,
    session_router,
    staff_router,
    products_router,
    members_router,
    tax_rates_router,
    transactions_router,
    discounts_router,
]
