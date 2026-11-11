from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.invoices import router as invoices_router
from app.db import init_db


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="InvoiceFlow", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(invoices_router)


@app.get("/health")
def health():
    return {"status": "ok"}