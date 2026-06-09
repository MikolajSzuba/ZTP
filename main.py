import os
from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.REST.data.database import (
    ensure_cart_schema_compatibility,
    ensure_notifications_schema_compatibility,
)
from app.REST.docs_app import product_docs_app
from app.REST.web.routes import router as products_router
from app.cart.docs_app import cart_docs_app
from app.cart.web.routes import router as cart_router
from app.identity.docs_app import identity_docs_app
from app.identity.web.routes import router as identity_router
from app.notifications.docs_app import notifications_docs_app
from app.notifications.service.notification_worker import run_worker
from app.notifications.web.routes import router as notifications_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_notifications_schema_compatibility()
    ensure_cart_schema_compatibility()
    if os.getenv("DISABLE_NOTIFICATION_WORKER", "0") != "1":
        thread = Thread(target=run_worker, daemon=True)
        thread.start()
    yield


app = FastAPI(title="Laboratorium 10 - React Frontend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(notifications_router)
app.include_router(identity_router)
app.include_router(cart_router)

app.mount("/products-docs", product_docs_app)
app.mount("/notifications-docs", notifications_docs_app)
app.mount("/identity-docs", identity_docs_app)
app.mount("/cart-docs", cart_docs_app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
