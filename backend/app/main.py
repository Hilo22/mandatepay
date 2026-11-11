import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_mandate import router as mandate_router
from app.api.routes_transactions import router as transactions_router
from app.api.routes_webhooks import router as webhooks_router
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "MandatePay Runtime Core: Programmable Financial Guardrails, "
        "Deterministic Prompt Injection Shield, Contract Assertion Runner, "
        "and Off-Chain Netting Ledger for Agentic Commerce."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mandate_router)
app.include_router(transactions_router)
app.include_router(webhooks_router)


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "paypal_mode": settings.PAYPAL_MODE,
    }

