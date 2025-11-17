# Backend/storage.py
"""
Handles all file I/O for the Expense Tracker.
Keeps persistence logic separate from core application logic.
"""

import json
import shutil
from pathlib import Path
from typing import List
from Backend.models import Expense

# -------------------------------
# Paths and Directories
# -------------------------------
# IMPORTANT:
# Backend/
#   storage.py  ← this file
#   data/       ← data directory (INSIDE Backend folder)
#
# BASE_DIR = Backend folder
# DATA_DIR = Backend/data/
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent  # Backend folder
DATA_DIR = BASE_DIR / "data"

EXPENSES_FILE = DATA_DIR / "expenses.json"
BACKUP_FILE = DATA_DIR / "expenses_backup.json"
BUDGET_FILE = DATA_DIR / "budget.json"


class JsonStorage:
    """Handles safe reading/writing of expense and budget data."""

    def __init__(self, data_file: Path = EXPENSES_FILE):
        self.data_file = data_file
        self.expenses: List[Expense] = []
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------
    # Expenses
    # -------------------------------
    def load_expenses(self) -> List[Expense]:
        """Load all expenses from the JSON file into memory."""
        if not self.data_file.exists():
            print(f"⚠️ No data file found at {self.data_file}; starting empty.")
            self.expenses = []
            self.save_expenses([])  # create empty file
            return self.expenses

        try:
            with self.data_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.expenses = [Expense.from_dict(item) for item in data]
        except json.JSONDecodeError as e:
            print(f"❌ Corrupted JSON in {self.data_file}: {e}. Resetting file.")
            self.expenses = []
            self.save_expenses([])
        return self.expenses

    def save_expenses(self, expenses: List[Expense]) -> None:
        """Save provided list of expenses to disk (atomic + backup)."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Backup before overwriting
        if self.data_file.exists():
            try:
                shutil.copy2(self.data_file, BACKUP_FILE)
            except Exception as e:
                print(f"⚠️ Backup failed: {e}")

        # Atomic write
        tmp_file = self.data_file.with_suffix(".tmp")
        with tmp_file.open("w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in expenses], f, indent=2)
        tmp_file.replace(self.data_file)
        self.expenses = expenses  # keep internal copy synced

    # -------------------------------
    # CRUD Helpers
    # -------------------------------
    def add_expense(self, expense: Expense) -> None:
        """Append a new Expense and persist."""
        self.expenses.append(expense)
        self.save_expenses(self.expenses)

    def replace_all(self, expenses: List[Expense]) -> None:
        """Replace all expenses (used for filters or reset)."""
        self.save_expenses(expenses)

    # -------------------------------
    # Budget handling
    # -------------------------------
    def save_budget(self, monthly_budget: float) -> None:
        """Save or update monthly budget."""
        try:
            with BUDGET_FILE.open("w", encoding="utf-8") as f:
                json.dump({"monthly_budget": monthly_budget}, f, indent=2)
            print(f"✅ Monthly budget saved to {BUDGET_FILE}")
        except Exception as e:
            print(f"❌ Failed to save budget: {e}")

    def load_budget(self) -> float:
        """Load the monthly budget if it exists."""
        if not BUDGET_FILE.exists():
            return 0.0
        try:
            with BUDGET_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return float(data.get("monthly_budget", 0.0))
        except Exception as e:
            print(f"⚠️ Could not read budget: {e}")
            return 0.0

    # -------------------------------
    # Update/Delete Expense
    # -------------------------------
    def update_expense(self, expense_id: str, **updates) -> bool:
        """Update fields of an existing expense."""
        for expense in self.expenses:
            if expense.id == expense_id:
                for key, value in updates.items():
                    if hasattr(expense, key) and value is not None:
                        setattr(expense, key, value)
                self.save_expenses(self.expenses)
                return True
        return False

    def delete_expense(self, expense_id: str) -> bool:
        """Delete an expense by ID."""
        before = len(self.expenses)
        new_expenses = [e for e in self.expenses if e.id != expense_id]
        if len(new_expenses) < before:
            self.save_expenses(new_expenses)
            return True
        return False
