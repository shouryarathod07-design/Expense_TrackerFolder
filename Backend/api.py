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
        VERCEL_FRONTEND,          # production frontend
    ],
    allow_credentials=True,       # REQUIRED for OAuth cookies
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
# 💰 Budget storage (still JSON-based, not critical)
# ------------------------------------------------------
_budget_store = JsonStorage()  # we ONLY use its budget methods


def load_budget() -> float:
    return _budget_store.load_budget()


def save_budget(value: float) -> None:
    _budget_store.save_budget(value)


# ------------------------------------------------------
# Small helper: convert DB rows → domain Expense objects
# (for reuse in search/report logic)
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
    return {
        "redirect": os.getenv("GOOGLE_REDIRECT_URI")
    }

# ------------------------------------------------------
# 📦 Expenses CRUD (DB-backed)
# ------------------------------------------------------
@app.get("/expenses", response_model=List[ExpenseRead])
async def list_expenses(session: AsyncSession = Depends(get_session)):
    db_expenses = await crud.get_expenses(session)
    return db_expenses


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
        db_expense = await crud.create_expense(session, expense)
        return db_expense
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
# 🔍 Search (uses DB + your existing fuzzy filter)
# ------------------------------------------------------
@app.get("/expenses/search", response_model=List[dict])
async def search_expenses(
    name: Optional[str] = Query("", description="Search by partial name"),
    category: Optional[str] = Query("", description="Filter by category"),
    date: Optional[str] = Query("", description="Filter by YYYY-MM-DD or YYYY-MM"),
    fuzzy_threshold: int = Query(65, description="Fuzzy match threshold (0–100)"),
    session: AsyncSession = Depends(get_session),
):
    logger.debug(
        f"[DEBUG] 🔍 Search route hit: name='{name}', "
        f"category='{category}', date='{date}'"
    )

    domain_expenses = await _load_all_domain_expenses(session)
    categories = [category] if category else []

    results = search_filter(domain_expenses, name, categories, date, fuzzy_threshold)
    logger.debug(f"[DEBUG] ✅ Found {len(results)} matching results")
    return [e.to_dict() for e in results]

# ------------------------------------------------------
# 📤 Export to CSV (uses DB → domain → CSV)
# ------------------------------------------------------
@app.post("/expenses/export")
async def export_expenses_to_csv(
    append: bool = True,
    session: AsyncSession = Depends(get_session),
):
    try:
        domain_expenses = await _load_all_domain_expenses(session)
        file_path = export_to_csv(domain_expenses, append=append)
        if not file_path:
            raise HTTPException(status_code=500, detail="Export failed.")

        return FileResponse(
            path=file_path,
            media_type="text/csv",
            filename="expenses_export.csv",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")

# ------------------------------------------------------
# 📊 Charts (DB → domain → your existing chart funcs)
# ------------------------------------------------------
@app.post("/charts/monthly")
async def generate_monthly_chart(
    year: int,
    session: AsyncSession = Depends(get_session),
):
    domain_expenses = await _load_all_domain_expenses(session)
    file_path = monthly_spending_chart(domain_expenses, year)
    if not file_path:
        raise HTTPException(status_code=400, detail="Chart generation failed.")
    return {"message": "✅ Chart generated", "file_path": str(file_path)}


@app.post("/charts/pie")
async def generate_category_pie(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
):
    domain_expenses = await _load_all_domain_expenses(session)
    file_path = monthly_spending_category_pie(domain_expenses, year, month)
    if not file_path:
        raise HTTPException(status_code=400, detail="Pie chart generation failed.")
    return {"message": "✅ Pie chart generated", "file_path": str(file_path)}

# ------------------------------------------------------
# 📈 Reports — SUMMARY (DB → domain → existing logic)
# ------------------------------------------------------
@app.get("/reports/summary")
async def get_reports_summary(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    try:
        domain_expenses = await _load_all_domain_expenses(session)

        # filter by year/month if provided (like before)
        if year and month:
            domain_expenses = [
                e
                for e in domain_expenses
                if e.expense_date.year == year and e.expense_date.month == month
            ]

        if not domain_expenses:
            return jsonable_encoder(
                {
                    "total": 0,
                    "avg_per_day": 0,
                    "per_category": {},
                    "message": "⚠️ No expenses found for that period.",
                }
            )

        total = sum((e.price for e in domain_expenses), Decimal("0"))

        min_d = min(e.expense_date for e in domain_expenses)
        max_d = max(e.expense_date for e in domain_expenses)
        days = (max_d - min_d).days + 1
        avg_per_day = total / days if days > 0 else Decimal("0")

        per_category = defaultdict(Decimal)
        for e in domain_expenses:
            per_category[e.category] += e.price

        # full summaries (no year/month filter)
        if not (year and month):
            monthly = monthly_summary(domain_expenses)
            weekly = weekly_summary(domain_expenses)
            annual = annual_summary(domain_expenses)

            def safe_monthly_dict(data):
                return {f"{y}-{m:02d}": float(t) for (y, m), t in data.items()}

            def safe_weekly_dict(data):
                return {
                    f"{y}-W{w:02d}": {
                        "total": float(v["total"]),
                        "start": v["start"].isoformat() if v["start"] else None,
                        "end": v["end"].isoformat() if v["end"] else None,
                    }
                    for (y, w), v in data.items()
                }

            def safe_annual_dict(data):
                return {str(y): float(t) for y, t in data.items()}

            return jsonable_encoder(
                {
                    "total": float(total),
                    "avg_per_day": float(avg_per_day),
                    "per_category": {k: float(v) for k, v in per_category.items()},
                    "monthly_summary": safe_monthly_dict(monthly),
                    "weekly_summary": safe_weekly_dict(weekly),
                    "annual_summary": safe_annual_dict(annual),
                }
            )

        # month-specific summary
        month_name = datetime(year, month, 1).strftime("%B")
        return jsonable_encoder(
            {
                "period": f"{month_name} {year}",
                "total": float(total),
                "avg_per_day": float(avg_per_day),
                "days": days,
                "per_category": {k: float(v) for k, v in per_category.items()},
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")

# ------------------------------------------------------
# ⚡ Reports — QUICK GLANCE (DB expenses + JSON budget)
# ------------------------------------------------------
@app.get("/reports/quick")
async def get_quick_glance(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        monthly_budget = load_budget()

        if monthly_budget is None:
            raise ValueError("No budget data found. Please set a monthly budget first.")

        if not isinstance(monthly_budget, Decimal):
            monthly_budget = Decimal(str(monthly_budget))

        domain_expenses = await _load_all_domain_expenses(session)

        indicator = quick_indicator(domain_expenses, year, month, monthly_budget)
        top_category = quick_top_category(domain_expenses, year, month)
        month_change = quick_month_over_month_change(domain_expenses, year, month)
        burn_rate = quick_daily_burn_rate(domain_expenses, year, month)

        response = {
            "year": year,
            "month": month,
            "budget": float(monthly_budget),
            "indicator": indicator,
            "top_category": top_category,
            "month_change": month_change,
            "burn_rate": burn_rate,
        }

        return jsonable_encoder(response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick glance failed: {e}")
