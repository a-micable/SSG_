from fastapi import FastAPI
from .api.routes import router as api_router
from .db import init_db


app = FastAPI(title="Code Quality Platform - Backend")


@app.on_event("startup")
def startup_event():
    # initialize DB (for MVP use create_all)
    init_db()


app.include_router(api_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
