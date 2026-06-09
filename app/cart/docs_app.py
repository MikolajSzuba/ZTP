from fastapi import FastAPI

from app.cart.web.routes import router as cart_router

cart_docs_app = FastAPI(
    title="Cart and Orders API",
    docs_url="/",
    redoc_url=None,
    openapi_url="/openapi.json",
)

cart_docs_app.include_router(cart_router)
