from fastapi import FastAPI

from app.REST.docs_app import product_docs_app
from app.REST.web.routes import router as products_router
from app.notifications.docs_app import notifications_docs_app
from app.notifications.web.routes import router as notifications_router


app = FastAPI(title="Laboratorium 4 - Powiadomienia")

app.include_router(products_router)
app.include_router(notifications_router)

app.mount("/products-docs", product_docs_app)
app.mount("/notifications-docs", notifications_docs_app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
