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

from datetime import datetime
from collections import defaultdict

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Depends,
)
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy.ext.asyncio import AsyncSession

# ------------------------------------------------------
# ✅ Ensure project root is in sys.path (for imports)
# ------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
print(f"[DEBUG] ✅ Added project root: {PROJECT_ROOT}", flush=True)

# ------------------------------------------------------
# ✅ Imports AFTER path fix
# ------------------------------------------------------
from Backend.schemas import ExpenseCreate, ExpenseUpdate, ExpenseRead
from Backend.models import Expense  # domain model (in-memory)
from Backend.storage import JsonStorage  # now used ONLY for budget
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

from Backend.db import get_session, engine, Base
from Backend.models_sql import ExpenseDB
from Backend import crud

from fastapi.responses import FileResponse

# ------------------------------------------------------
# ✅ Logging Setup
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
# ✅ FastAPI App + Session Middleware (Google OAuth)
# ------------------------------------------------------
app = FastAPI(title="Expense Tracker API", version="1.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "SHREK"),
)

# Routers
from Backend.auth import router as auth_router
app.include_router(auth_router)

from Backend.routes import ocr
app.include_router(ocr.router)

# ------------------------------------------------------
# 🚀 CORS — localhost + Vercel frontend
# ------------------------------------------------------
VERCEL_FRONTEND = "https://expense-tracker-frontend-olive.vercel.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # local dev
        VERCEL_FRONTEND,          # production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------
# 🧠 Budget storage (still JSON for now)
# ------------------------------------------------------
budget_store = JsonStorage()  # we only use its budget methods now

# ------------------------------------------------------
# 🗄️ DB startup: create tables if needed
# ------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    from sqlalchemy.exc import SQLAlchemyError

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[DB] ✅ Tables created / verified")
    except SQLAlchemyError as e:
        print(f"[DB] ❌ Error creating tables: {e}")


# ------------------------------------------------------
# 🔁 Helper: load all expenses from DB and adapt to domain model
# ------------------------------------------------------
async def load_all_expenses_as_domain(session: AsyncSession) -> List[Expense]:
    """
    Read all ExpenseDB rows from PostgreSQL and convert them into
    the in-memory Expense domain model so your existing reporting
    utilities (quick_indicator, monthly_summary, etc.) keep working
    unchanged.
    """
    db_expenses = await crud.get_expenses(session)
    domain_expenses: List[Expense] = []

    for e in db_expenses:
        domain_expenses.append(
            Expense(
                id=str(e.id),
                name=e.name,
                price=e.price,
                expense_date=e.expense_date,
                category=e.category,
                note=e.note,
            )
        )

    return domain_expenses


# ------------------------------------------------------
# ✅ Health Check
# ------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running 🚀"}


# TEMP debug route
@app.get("/test-env")
def test_env():
    return {"redirect": os.getenv("GOOGLE_REDIRECT_URI")}


# ------------------------------------------------------
# ✅ List All Expenses
# ------------------------------------------------------
@app.get("/expenses", response_model=List[ExpenseRead])
async def list_expenses(session: AsyncSession = Depends(get_session)):
    expenses = await crud.get_expenses(session)
    # Convert DB model → Pydantic schema
    return [
        ExpenseRead(
            id=str(e.id),
            name=e.name,
            category=e.category,
            price=e.price,
            expense_date=e.expense_date,
            note=e.note,
        )
        for e in expenses
    ]


# ------------------------------------------------------
# ✅ Search & Filter (DB-backed now)
# ------------------------------------------------------
@app.get("/expenses/search", response_model=List[ExpenseRead])
async def search_expenses(
    name: Optional[str] = Query("", description="Search by partial name"),
    category: Optional[str] = Query("", description="Filter by category"),
    date: Optional[str] = Query("", description="Filter by YYYY-MM-DD or YYYY-MM"),
    fuzzy_threshold: int = Query(65, description="Fuzzy match threshold (0–100)"),
    session: AsyncSession = Depends(get_session),
):
    print(
        f"[DEBUG] 🔍 Search route hit: name='{name}', "
        f"category='{category}', date='{date}'"
    )

    # Load all expenses from DB as domain objects
    all_expenses = await load_all_expenses_as_domain(session)

    categories = [category] if category else []
    results = search_filter(all_expenses, name, categories, date, fuzzy_threshold)

    # Convert domain → Pydantic
    return [
        ExpenseRead(
            id=e.id,
            name=e.name,
            category=e.category,
            price=e.price,
            expense_date=e.expense_date,
            note=e.note,
        )
        for e in results
    ]


# ------------------------------------------------------
# ✅ Get Expense by ID
# ------------------------------------------------------
@app.get("/expenses/id/{expense_id}", response_model=ExpenseRead)
async def get_expense(
    expense_id: str,
    session: AsyncSession = Depends(get_session),
):
    db_expense = await crud.get_expense_by_id(session, expense_id)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    return ExpenseRead(
        id=str(db_expense.id),
        name=db_expense.name,
        category=db_expense.category,
        price=db_expense.price,
        expense_date=db_expense.expense_date,
        note=db_expense.note,
    )


# ------------------------------------------------------
# ✅ Add New Expense
# ------------------------------------------------------
@app.post("/expenses", response_model=ExpenseRead)
async def add_expense(
    expense: ExpenseCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        db_expense = await crud.create_expense(session, expense)
        return ExpenseRead(
            id=str(db_expense.id),
            name=db_expense.name,
            category=db_expense.category,
            price=db_expense.price,
            expense_date=db_expense.expense_date,
            note=db_expense.note,
        )
    except Exception as e:
        logger.error(f"[ERROR] Failed to add expense: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to add expense: {e}")


# ------------------------------------------------------
# ✅ Export Expenses to CSV
# ------------------------------------------------------
@app.post("/expenses/export")
async def export_expenses_to_csv(
    append: bool = True,
    session: AsyncSession = Depends(get_session),
):
    """
    Export all expenses to CSV.
    Returns a downloadable CSV file.
    """
    try:
        # Load from DB, adapt to domain for export util
        domain_expenses = await load_all_expenses_as_domain(session)
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
# ✅ Charts Endpoints (still file-based output)
# ------------------------------------------------------
@app.post("/charts/monthly")
async def generate_monthly_chart(
    year: int,
    session: AsyncSession = Depends(get_session),
):
    """Generate monthly spending vs budget chart."""
    domain_expenses = await load_all_expenses_as_domain(session)
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
    """Generate monthly category pie chart."""
    domain_expenses = await load_all_expenses_as_domain(session)
    file_path = monthly_spending_category_pie(domain_expenses, year, month)
    if not file_path:
        raise HTTPException(status_code=400, detail="Pie chart generation failed.")
    return {"message": "✅ Pie chart generated", "file_path": str(file_path)}


# ------------------------------------------------------
# ✅ Detailed Summary Reports
# ------------------------------------------------------
@app.get("/reports/summary")
async def get_reports_summary(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """
    Return detailed expense summary for the given month/year.
    If no month/year is provided, return full summaries.
    """
    try:
        all_expenses = await load_all_expenses_as_domain(session)

        # Filtered subset for specific year/month
        expenses = all_expenses
        if year and month:
            expenses = [
                e
                for e in all_expenses
                if e.expense_date.year == year and e.expense_date.month == month
            ]

        if not expenses:
            return jsonable_encoder(
                {
                    "total": 0,
                    "avg_per_day": 0,
                    "per_category": {},
                    "message": "⚠️ No expenses found for that period.",
                }
            )

        # Total & average per day
        total = sum((e.price for e in expenses), Decimal("0"))

        min_d = min(e.expense_date for e in expenses)
        max_d = max(e.expense_date for e in expenses)
        days = (max_d - min_d).days + 1
        avg_per_day = total / days if days > 0 else Decimal("0")

        per_category = defaultdict(Decimal)
        for e in expenses:
            per_category[e.category] += e.price

        # If no period requested → full dataset summaries
        if not (year and month):
            monthly = monthly_summary(all_expenses)
            weekly = weekly_summary(all_expenses)
            annual = annual_summary(all_expenses)

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
                    "per_category": {
                        k: float(v) for k, v in per_category.items()
                    },
                    "monthly_summary": safe_monthly_dict(monthly),
                    "weekly_summary": safe_weekly_dict(weekly),
                    "annual_summary": safe_annual_dict(annual),
                }
            )

        # Month-specific summary
        month_name = datetime(year, month, 1).strftime("%B")
        return jsonable_encoder(
            {
                "period": f"{month_name} {year}",
                "total": float(total),
                "avg_per_day": float(avg_per_day),
                "days": days,
                "per_category": {
                    k: float(v) for k, v in per_category.items()
                },
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")


# ------------------------------------------------------
# ✅ Quick Glance
# ------------------------------------------------------
@app.get("/reports/quick")
async def get_quick_glance(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Quick monthly overview combining key metrics:
      - Budget indicator (spent vs budget)
      - Top spending category
      - Month-over-month spending change
      - Average daily burn rate
    """
    try:
        monthly_budget = budget_store.load_budget()

        if monthly_budget is None:
            raise ValueError(
                "No budget data found. Please set a monthly budget first."
            )

        if not isinstance(monthly_budget, Decimal):
            monthly_budget = Decimal(str(monthly_budget))

        expenses = await load_all_expenses_as_domain(session)

        indicator = quick_indicator(expenses, year, month, monthly_budget)
        top_category = quick_top_category(expenses, year, month)
        month_change = quick_month_over_month_change(expenses, year, month)
        burn_rate = quick_daily_burn_rate(expenses, year, month)

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


# ------------------------------------------------------
# ✅ Update Existing Expense
# ------------------------------------------------------
@app.put("/expenses/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: str,
    payload: ExpenseUpdate,
    session: AsyncSession = Depends(get_session),
):
    db_expense = await crud.update_expense(session, expense_id, payload)
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    return ExpenseRead(
        id=str(db_expense.id),
        name=db_expense.name,
        category=db_expense.category,
        price=db_expense.price,
        expense_date=db_expense.expense_date,
        note=db_expense.note,
    )


# ------------------------------------------------------
# ✅ Delete Expense
# ------------------------------------------------------
@app.delete("/expenses/{expense_id}")
async def delete_expense(
    expense_id: str,
    session: AsyncSession = Depends(get_session),
):
    success = await crud.delete_expense(session, expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"message": f"Expense {expense_id} deleted successfully."}
