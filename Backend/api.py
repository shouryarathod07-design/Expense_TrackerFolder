# ===============================
# Backend/api.py
# Expense Tracker FastAPI Backend
# ===============================
from dotenv import load_dotenv
import os
load_dotenv()

import sys
import os
import logging
from decimal import Decimal
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from collections import defaultdict
from decimal import Decimal
from Backend.schemas import ExpenseCreate
from starlette.middleware.sessions import SessionMiddleware

# ------------------------------------------------------
# ✅ Ensure project root is in sys.path (for imports)
# ------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
print(f"[DEBUG] ✅ Added project root: {PROJECT_ROOT}", flush=True)

# ------------------------------------------------------
# Imports AFTER path fix
# ------------------------------------------------------
from Backend.models import Expense
from Backend.storage import JsonStorage
from Backend.reports import quick_indicator, quick_top_category, quick_daily_burn_rate, quick_month_over_month_change
from Backend.filters import search_filter
from Backend.reports import (
    monthly_summary,
    weekly_summary,
    annual_summary,
    monthly_summary_compare_budget,
)
from Backend.charts import (
    monthly_spending_chart,
    monthly_spending_category_pie,
)
from Backend.export import export_to_csv

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

# Routers
from Backend.auth import router as auth_router
app.include_router(auth_router)

from Backend.routes import ocr
app.include_router(ocr.router)

# ------------------------------------------------------
# 🚀 FIXED CORS — includes Vercel URL
# ------------------------------------------------------
VERCEL_FRONTEND = "https://expense-tracker-frontend-olive.vercel.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # local dev
        VERCEL_FRONTEND,            # production frontend
    ],
    allow_credentials=True,         # REQUIRED for OAuth cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------
# Shared store
# ------------------------------------------------------
store = JsonStorage()
store.load_expenses()
print(f"[DEBUG] 🚀 Loaded {len(store.expenses)} expenses into memory.", flush=True)

# ------------------------------------------------------
# Health check
# ------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running 🚀"}

# TEMP debug route
@app.get("/test-env")
def test_env():
    return {
        "redirect": os.getenv("GOOGLE_REDIRECT_URI")
    }

# ------------------------------------------------------
# Expense CRUD and Reports (UNCHANGED)
# ------------------------------------------------------
@app.get("/expenses", response_model=List[dict])
def list_expenses():
    logger.debug(f"Listing all expenses ({len(store.expenses)})")
    return [e.to_dict() for e in store.expenses]

@app.get("/expenses/search", response_model=List[dict])
def search_expenses(
    name: Optional[str] = Query("", description="Search by partial name"),
    category: Optional[str] = Query("", description="Filter by category"),
    date: Optional[str] = Query("", description="Filter by YYYY-MM-DD or YYYY-MM"),
    fuzzy_threshold: int = Query(65, description="Fuzzy match threshold (0–100)"),
):
    print(f"[DEBUG] 🔍 Search route hit successfully: name='{name}', category='{category}', date='{date}'")

    categories = [category] if category else []
    logger.debug(f"[DEBUG] 📦 Loaded {len(store.expenses)} expenses in memory")

    results = search_filter(store.expenses, name, categories, date, fuzzy_threshold)
    logger.debug(f"[DEBUG] ✅ Found {len(results)} matching results")

    return [e.to_dict() for e in results]

@app.get("/expenses/id/{expense_id}", response_model=dict)
def get_expense(expense_id: str):
    for e in store.expenses:
        if e.id == expense_id:
            return e.to_dict()
    raise HTTPException(status_code=404, detail="Expense not found")

@app.post("/expenses", response_model=dict)
def add_expense(expense: ExpenseCreate):
    try:
        new_expense = Expense(
            name=expense.name,
            price=Decimal(expense.price),
            expense_date=expense.expense_date,
            category=expense.category,
            note=expense.note
        )
        store.add_expense(new_expense)
        return new_expense.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add expense: {e}")

from fastapi.responses import FileResponse

@app.post("/expenses/export")
def export_expenses_to_csv(append: bool = True):
    try:
        file_path = export_to_csv(store.expenses, append=append)
        if not file_path:
            raise HTTPException(status_code=500, detail="Export failed.")

        return FileResponse(
            path=file_path,
            media_type="text/csv",
            filename="expenses_export.csv"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")

@app.post("/charts/monthly")
def generate_monthly_chart(year: int):
    file_path = monthly_spending_chart(store.expenses, year)
    if not file_path:
        raise HTTPException(status_code=400, detail="Chart generation failed.")
    return {"message": "✅ Chart generated", "file_path": str(file_path)}

@app.post("/charts/pie")
def generate_category_pie(year: int, month: int):
    file_path = monthly_spending_category_pie(store.expenses, year, month)
    if not file_path:
        raise HTTPException(status_code=400, detail="Pie chart generation failed.")
    return {"message": "✅ Pie chart generated", "file_path": str(file_path)}

@app.get("/reports/summary")
def get_reports_summary(year: Optional[int] = Query(None), month: Optional[int] = Query(None)):
    try:
        expenses = store.expenses

        if year and month:
            expenses = [
                e for e in expenses
                if e.expense_date.year == year and e.expense_date.month == month
            ]

        if not expenses:
            return jsonable_encoder({
                "total": 0,
                "avg_per_day": 0,
                "per_category": {},
                "message": "⚠️ No expenses found for that period."
            })

        total = sum((e.price for e in expenses), Decimal("0"))

        min_d = min(e.expense_date for e in expenses)
        max_d = max(e.expense_date for e in expenses)
        days = (max_d - min_d).days + 1
        avg_per_day = total / days if days > 0 else Decimal("0")

        per_category = defaultdict(Decimal)
        for e in expenses:
            per_category[e.category] += e.price

        if not (year and month):
            monthly = monthly_summary(store.expenses)
            weekly = weekly_summary(store.expenses)
            annual = annual_summary(store.expenses)

            def safe_monthly_dict(data):
                return {
                    f"{y}-{m:02d}": float(t)
                    for (y, m), t in data.items()
                }

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

            return jsonable_encoder({
                "total": float(total),
                "avg_per_day": float(avg_per_day),
                "per_category": {k: float(v) for k, v in per_category.items()},
                "monthly_summary": safe_monthly_dict(monthly),
                "weekly_summary": safe_weekly_dict(weekly),
                "annual_summary": safe_annual_dict(annual),
            })

        month_name = datetime(year, month, 1).strftime("%B")
        return jsonable_encoder({
            "period": f"{month_name} {year}",
            "total": float(total),
            "avg_per_day": float(avg_per_day),
            "days": days,
            "per_category": {k: float(v) for k, v in per_category.items()},
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")

@app.get("/reports/quick")
def get_quick_glance(year: int, month: int):
    try:
        monthly_budget = store.load_budget()

        if monthly_budget is None:
            raise ValueError("No budget data found. Please set a monthly budget first.")

        if not isinstance(monthly_budget, Decimal):
            monthly_budget = Decimal(str(monthly_budget))

        indicator = quick_indicator(store.expenses, year, month, monthly_budget)
        top_category = quick_top_category(store.expenses, year, month)
        month_change = quick_month_over_month_change(store.expenses, year, month)
        burn_rate = quick_daily_burn_rate(store.expenses, year, month)

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

@app.put("/expenses/{expense_id}")
def update_expense(expense_id: str, payload: dict):
    expense = next((e for e in store.expenses if e.id == expense_id), None)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if "name" in payload:
        expense.name = payload["name"]
    if "price" in payload:
        expense.price = Decimal(str(payload["price"]))
    if "category" in payload:
        expense.category = payload["category"]
    if "expense_date" in payload:
        expense.expense_date = datetime.strptime(payload["expense_date"], "%Y-%m-%d").date()

    store.save_expenses(store.expenses)

    return {"message": "Expense updated", "expense": expense.to_dict()}

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str):
    success = store.delete_expense(expense_id)
    if not success:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"message": f"Expense {expense_id} deleted successfully."}
