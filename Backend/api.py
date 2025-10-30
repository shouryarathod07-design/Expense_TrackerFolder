# Backend/api.py
"""
FastAPI backend for Expense Tracker
Phase 1: Basic CRUD endpoints for expenses
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from decimal import Decimal
from typing import List
from Expense_TrackerFolder.Backend.storage import JsonStorage
from Expense_TrackerFolder.Backend.models import Expense


#debug
print("✅ FastAPI backend loaded successfully")

# -------------------------------------------------
# 1️⃣ App Setup
# -------------------------------------------------
app = FastAPI(title="Expense Tracker API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# 2️⃣ Pydantic Schema (for validation)
# -------------------------------------------------
class ExpenseIn(BaseModel):
    name: str
    price: Decimal
    expense_date: str
    category: str


class ExpenseOut(BaseModel):
    id: str
    name: str
    price: Decimal
    expense_date: str
    category: str


# -------------------------------------------------
# 3️⃣ Routes
# -------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "✅ Expense Tracker API is running!"}


@app.get("/expenses", response_model=List[ExpenseOut])
def list_expenses():
    """Get all expenses."""
    store = JsonStorage()
    expenses = store.load_expenses()
    return [e.to_dict() for e in expenses]


@app.post("/expenses", response_model=ExpenseOut)
def add_expense(expense: ExpenseIn):
    """Add a new expense."""
    store = JsonStorage()
    new_exp = Expense(
        name=expense.name,
        price=expense.price,
        expense_date=expense.expense_date,
        category=expense.category,
    )
    store.add_expense(new_exp)
    return new_exp.to_dict()
