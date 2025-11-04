# ===============================
# Backend/api.py
# Expense Tracker FastAPI Backend
# ===============================

import sys
import os
import logging
from decimal import Decimal
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder


# ------------------------------------------------------
# ✅ Ensure project root is in sys.path (for imports)
# ------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
print(f"[DEBUG] ✅ Added project root: {PROJECT_ROOT}", flush=True)

# ------------------------------------------------------
# ✅ Imports (after sys.path fix)
# ------------------------------------------------------
from Expense_TrackerFolder.Backend.models import Expense
from Expense_TrackerFolder.Backend.storage import JsonStorage
from Expense_TrackerFolder.Backend.reports import quick_indicator, quick_top_category,quick_daily_burn_rate,quick_month_over_month_change
from Expense_TrackerFolder.Backend.filters import search_filter
from Expense_TrackerFolder.Backend.reports import (
    monthly_summary,
    weekly_summary,
    annual_summary,
    monthly_summary_compare_budget,
)
from Expense_TrackerFolder.Backend.charts import (
    monthly_spending_chart,
    monthly_spending_category_pie,
)
from Expense_TrackerFolder.Backend.export import export_to_csv


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
# ✅ FastAPI App Setup
# ------------------------------------------------------
app = FastAPI(title="Expense Tracker API", version="1.0")

# Shared JSON storage instance
store = JsonStorage()
store.load_expenses()
print(f"[DEBUG] 🚀 Loaded {len(store.expenses)} expenses into memory.", flush=True)


# ------------------------------------------------------
# ✅ Health Check
# ------------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "Expense Tracker API is running 🚀"}


# ------------------------------------------------------
# ✅ List All Expenses
# ------------------------------------------------------
@app.get("/expenses", response_model=List[dict])
def list_expenses():
    logger.debug(f"Listing all expenses ({len(store.expenses)})")
    return [e.to_dict() for e in store.expenses]


# ------------------------------------------------------
# ✅ Search & Filter (Placed BEFORE /{expense_id})
# ------------------------------------------------------
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


# ------------------------------------------------------
# ✅ Get Expense by ID
# ------------------------------------------------------
@app.get("/expenses/id/{expense_id}", response_model=dict)
def get_expense(expense_id: str):
    """Note: now accessed via /expenses/id/{expense_id} to avoid collision with /search"""
    for e in store.expenses:
        if e.id == expense_id:
            logger.debug(f"[DEBUG] ✅ Found expense with ID {expense_id}")
            return e.to_dict()
    raise HTTPException(status_code=404, detail="Expense not found")


# ------------------------------------------------------
# ✅ Add New Expense
# ------------------------------------------------------
@app.post("/expenses", response_model=dict)
def add_expense(name: str, price: float, category: str, date: str):
    try:
        new_expense = Expense(name, Decimal(price), date, category)
        store.add_expense(new_expense)
        logger.debug(f"[DEBUG] 💾 Added new expense: {new_expense.to_dict()}")
        return new_expense.to_dict()
    except Exception as e:
        logger.error(f"[ERROR] Failed to add expense: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to add expense: {e}")
    

# exporting to csv endpoint


@app.post("/expenses/export")
def export_expenses_to_csv(append: bool = True):
    """Export all expenses to CSV (creates data/exports if missing)."""
    try:
        file_path = export_to_csv(store.expenses, append=append)
        if not file_path:
            raise HTTPException(status_code=500, detail="Export failed.")
        return {
            "message": "✅ Export successful",
            "file_path": str(file_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")
    


# charts endpoint

@app.post("/charts/monthly")
def generate_monthly_chart(year: int):
    """Generate monthly spending vs budget chart."""
    file_path = monthly_spending_chart(store.expenses, year)
    if not file_path:
        raise HTTPException(status_code=400, detail="Chart generation failed.")
    return {"message": "✅ Chart generated", "file_path": str(file_path)}

@app.post("/charts/pie")
def generate_category_pie(year: int, month: int):
    """Generate monthly category pie chart."""
    file_path = monthly_spending_category_pie(store.expenses, year, month)
    if not file_path:
        raise HTTPException(status_code=400, detail="Pie chart generation failed.")
    return {"message": "✅ Pie chart generated", "file_path": str(file_path)}

    

# reports endpoint
@app.get("/reports/summary")
def get_reports_summary():
    """
    Generate a clean, JSON-safe summary report (monthly, weekly, annual).
    Formats keys like '2025-10' instead of '(2025, 10)'.
    """
    try:
        monthly = monthly_summary(store.expenses)
        weekly = weekly_summary(store.expenses)
        annual = annual_summary(store.expenses)

        # -------------------------------
        # 🧩 Helper to format safe dicts
        # -------------------------------
        def safe_monthly_dict(data):
            return {
                f"{year}-{month:02d}": float(total)
                for (year, month), total in data.items()
            }

        def safe_weekly_dict(data):
            return {
                f"{year}-W{week:02d}": {
                    "total": float(values["total"]),
                    "start": values["start"].isoformat() if values["start"] else None,
                    "end": values["end"].isoformat() if values["end"] else None,
                }
                for (year, week), values in data.items()
            }

        def safe_annual_dict(data):
            return {str(year): float(total) for year, total in data.items()}

        # -------------------------------
        # 🧮 Build clean unified response
        # -------------------------------
        response = {
            "monthly_summary": safe_monthly_dict(monthly),
            "weekly_summary": safe_weekly_dict(weekly),
            "annual_summary": safe_annual_dict(annual),
        }

        return jsonable_encoder(response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {e}")


# quick glance endpoint 

@app.get("/reports/quick")
def get_quick_glance(year: int, month: int):
    """
    Quick monthly overview combining key metrics:
      - Budget indicator (spent vs budget)
      - Top spending category
      - Month-over-month spending change
      - Average daily burn rate
    """
    try:
        # ------------------------------------------
        # 1️⃣ Load budget from file (your JSON store)
        # ------------------------------------------
        monthly_budget = store.load_budget()

        # Handle None or invalid budget gracefully
        if monthly_budget is None:
            raise ValueError("No budget data found. Please set a monthly budget first.")

        # ------------------------------------------
        # 2️⃣ Normalize type (convert float → Decimal)
        # ------------------------------------------
        if not isinstance(monthly_budget, Decimal):
            monthly_budget = Decimal(str(monthly_budget))

        # ------------------------------------------
        # 3️⃣ Generate all quick glance metrics
        # ------------------------------------------
        indicator = quick_indicator(store.expenses, year, month, monthly_budget)
        top_category = quick_top_category(store.expenses, year, month)
        month_change = quick_month_over_month_change(store.expenses, year, month)
        burn_rate = quick_daily_burn_rate(store.expenses, year, month)

        # ------------------------------------------
        # 4️⃣ Build clean, JSON-safe response
        # ------------------------------------------
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
@app.put("/expenses/{expense_id}", response_model=dict)
def update_expense(
    expense_id: str,
    name: Optional[str] = None,
    price: Optional[float] = None,
    category: Optional[str] = None,
    date: Optional[str] = None,
):
    for e in store.expenses:
        if e.id == expense_id:
            if name:
                e.name = name
            if price:
                e.price = Decimal(price)
            if category:
                e.category = category
            if date:
                e.expense_date = date

            store.save_expenses(store.expenses)
            logger.debug(f"[DEBUG] ✏️ Updated expense {expense_id}")
            return e.to_dict()

    raise HTTPException(status_code=404, detail="Expense not found")


# ------------------------------------------------------
# ✅ Delete Expense
# ------------------------------------------------------
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str):
    success = store.delete_expense(expense_id)
    if not success:
        logger.warning(f"[WARN] Attempted to delete non-existent expense {expense_id}")
        raise HTTPException(status_code=404, detail="Expense not found")
    logger.debug(f"[DEBUG] 🗑️ Deleted expense {expense_id}")
    return {"message": f"Expense {expense_id} deleted successfully."}






    