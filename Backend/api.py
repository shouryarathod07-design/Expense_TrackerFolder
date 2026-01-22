# ===============================
# Backend/api.py
# Expense Tracker FastAPI Backend
# ===============================
from dotenv import load_dotenv
import os

load_dotenv()

import sys
import logging
from decimal import Decimal
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import FileResponse
from datetime import datetime
from collections import defaultdict

# ------------------------------------------------------
# ✅ Ensure project root is in sys.path (for imports)
# ------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
print(f"[DEBUG] ✅ Added project root: {PROJECT_ROOT}", flush=True)

# ------------------------------------------------------
# 🗄  DB + Models + CRUD
# ------------------------------------------------------
from sqlalchemy.ext.asyncio import AsyncSession
from Backend.db import engine, Base, get_session
from Backend.models_sql import ExpenseDB
from Backend import crud

# Domain model (for reports / filters)
from Backend.models import Expense

# Schemas (Pydantic)
from Backend.schemas import ExpenseCreate, ExpenseUpdate, ExpenseRead

# Existing analytics helpers
from Backend.reports import (
    quick_indicator,
    quick_top_category,
    quick_daily_burn_rate,
    quick_month_over_month_change,
    monthly_summary,
    weekly_summary,
    annual_summary,
)
from Backend.filters import search_filter
from Backend.charts import (
    monthly_spending_chart,
    monthly_spending_category_pie,
)
from Backend.export import export_to_csv

# JSON storage kept ONLY for budget
from Backend.storage import JsonStorage

# ------------------------------------------------------
# Logging Setup
# ------------------------------------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("expense_tracker")

if not logger.handlers:
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console.setFormatter(formatter)
    logger.addHandler(console)

logger.setLevel(logging.DEBUG)

# ------------------------------------------------------
# FastAPI App + Session Middleware (Required for Google OAuth)
# ------------------------------------------------------
app = FastAPI(title="Expense Tracker API", version="1.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "SHREK"),
)

# ------------------------------------------------------
# OAuth + OCR Routers
# ------------------------------------------------------
from Backend.auth import router as auth_router
from Backend.routes import ocr

app.include_router(auth_router)
app.include_router(ocr.router)

# ------------------------------------------------------
# 🚀 CORS — includes Vercel URL
# ------------------------------------------------------
VERCEL_FRONTEND = "https://expense-tracker-frontend-olive.vercel.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # local dev
        VERCEL_FRONTEND,
        "https://expense-tracker-backend-sdjo.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------
# 🧱 DB startup: create tables if missing
# ------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables ensured")

# ------------------------------------------------------
# 💰 Budget storage (JSON-backed)
# ------------------------------------------------------
from pydantic import BaseModel, Field

_budget_store = JsonStorage()  # ONLY budget methods are used


def load_budget() -> float:
    return _budget_store.load_budget()


def save_budget(value: float) -> None:
    _budget_store.save_budget(value)


class BudgetPayload(BaseModel):
    budget: float = Field(..., gt=0, description="Monthly budget (> 0)")


@app.get("/budget")
def get_budget():
    """
    Return the current monthly budget.
    If none exists yet, initialize to a sane default (500).
    """
    budget = load_budget()

    if budget is None:
        budget = 500
        save_budget(budget)

    return {"budget": float(budget)}


@app.put("/budget")
def update_budget(payload: BudgetPayload):
    """
    Update the monthly budget.
    """
    save_budget(payload.budget)
    return {"budget": float(payload.budget)}

# ------------------------------------------------------
# Small helper: convert DB rows → domain Expense objects
# ------------------------------------------------------
def _to_domain(exp: ExpenseDB) -> Expense:
    return Expense(
        id=str(exp.id),
        name=exp.name,
        price=Decimal(str(exp.price)),
        expense_date=exp.expense_date,
        category=exp.category,
        note=exp.note,
    )


async def _load_all_domain_expenses(session: AsyncSession) -> List[Expense]:
    db_expenses = await crud.get_expenses(session)
    return [_to_domain(e) for e in db_expenses]

# ------------------------------------------------------
# ✅ Health check
# ------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running 🚀"}


@app.get("/test-env")
def test_env():
    return {"redirect": os.getenv("GOOGLE_REDIRECT_URI")}

# ------------------------------------------------------
# 📦 Expenses CRUD (DB-backed)
# ------------------------------------------------------
@app.get("/expenses", response_model=List[ExpenseRead])
async def list_expenses(session: AsyncSession = Depends(get_session)):
    return await crud.get_expenses(session)


@app.get("/expenses/id/{expense_id}", response_model=ExpenseRead)
async def get_expense(
    expense_id: str, session: AsyncSession = Depends(get_session)
):
    db_expense = await crud.get_expense_by_id(session, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return db_expense


@app.post("/expenses", response_model=ExpenseRead)
async def add_expense(
    expense: ExpenseCreate, session: AsyncSession = Depends(get_session)
):
    try:
        return await crud.create_expense(session, expense)
    except Exception as e:
        logger.exception("Failed to add expense")
        raise HTTPException(status_code=400, detail=f"Failed to add expense: {e}")


@app.put("/expenses/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: str,
    payload: ExpenseUpdate,
    session: AsyncSession = Depends(get_session),
):
    db_expense = await crud.update_expense(session, expense_id, payload)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return db_expense


@app.delete("/expenses/{expense_id}")
async def delete_expense(
    expense_id: str,
    session: AsyncSession = Depends(get_session),
):
    success = await crud.delete_expense(session, expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": f"Expense {expense_id} deleted successfully."}

# ------------------------------------------------------
# 🔍 Search
# ------------------------------------------------------
@app.get("/expenses/search", response_model=List[dict])
async def search_expenses(
    name: Optional[str] = Query(""),
    category: Optional[str] = Query(""),
    date: Optional[str] = Query(""),
    fuzzy_threshold: int = Query(65),
    session: AsyncSession = Depends(get_session),
):
    domain_expenses = await _load_all_domain_expenses(session)
    categories = [category] if category else []
    results = search_filter(domain_expenses, name, categories, date, fuzzy_threshold)
    return [e.to_dict() for e in results]

# ------------------------------------------------------
# 📤 Export to CSV
# ------------------------------------------------------
@app.post("/expenses/export")
async def export_expenses_to_csv(
    append: bool = True,
    session: AsyncSession = Depends(get_session),
):
    domain_expenses = await _load_all_domain_expenses(session)
    file_path = export_to_csv(domain_expenses, append=append)
    if not file_path:
        raise HTTPException(status_code=500, detail="Export failed.")
    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename="expenses_export.csv",
    )

# ------------------------------------------------------
# 📈 Reports — QUICK GLANCE
# ------------------------------------------------------
@app.get("/reports/quick")
async def get_quick_glance(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
):
    monthly_budget = load_budget()
    if monthly_budget is None:
        raise ValueError("No budget data found.")

    monthly_budget = Decimal(str(monthly_budget))
    domain_expenses = await _load_all_domain_expenses(session)

    return jsonable_encoder(
        {
            "year": year,
            "month": month,
            "budget": float(monthly_budget),
            "indicator": quick_indicator(domain_expenses, year, month, monthly_budget),
            "top_category": quick_top_category(domain_expenses, year, month),
            "month_change": quick_month_over_month_change(domain_expenses, year, month),
            "burn_rate": quick_daily_burn_rate(domain_expenses, year, month),
        }
    )