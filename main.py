import os
from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI

from app.REST.data.database import ensure_notifications_schema_compatibility
from app.REST.docs_app import product_docs_app
from app.REST.web.routes import router as products_router
from app.notifications.docs_app import notifications_docs_app
from app.notifications.service.notification_worker import run_worker
from app.notifications.web.routes import router as notifications_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_notifications_schema_compatibility()
    if os.getenv("DISABLE_NOTIFICATION_WORKER", "0") != "1":
        thread = Thread(target=run_worker, daemon=True)
        thread.start()
    yield


app = FastAPI(title="Laboratorium 5 - Powiadomienia", lifespan=lifespan)

app.include_router(products_router)
app.include_router(notifications_router)

app.mount("/products-docs", product_docs_app)
app.mount("/notifications-docs", notifications_docs_app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
