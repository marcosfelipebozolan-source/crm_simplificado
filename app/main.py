from fastapi import FastAPI
from .database import create_db_and_tables
from .routers.companies import router as companies_router
from .routers.contacts  import router as contacts_router
from .routers.deals     import router as deals_router

app = FastAPI(title="CRM Simplificado", version="0.1.0")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def root():
    return {"ok": True, "app": "CRM", "version": "0.1.0"}

app.include_router(companies_router)
app.include_router(contacts_router)
app.include_router(deals_router)
