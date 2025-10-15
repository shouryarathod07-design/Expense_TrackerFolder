# Solely to keep file handling i/o separate from the rest of the core app logic 
#imports:

import json
from models import Expense


#main part:...

import json, os, shutil
from pathlib import Path
from models import Expense

# Resolve to your project folder where storage.py lives:
BASE_DIR = Path(__file__).resolve().parent            # Expense_TrackerFolder
DATA_DIR  = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "expenses.json"
BACKUP_FILE = DATA_DIR / "expenses_backup.json"

def save_expense(expenses, filename: Path = DATA_FILE):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # backup old file before overwrite
    if filename.exists():
        try:
            shutil.copy2(filename, BACKUP_FILE)
        except Exception:
            pass
    # atomic-ish write via temp file
    tmp = filename.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in expenses], f, indent=2)
    tmp.replace(filename)
    # optional debug:
    # print(f"[DEBUG] Saved {len(expenses)} expenses to {filename}")

def load_expense(filename: Path = DATA_FILE):
    try:
        with filename.open("r", encoding="utf-8") as f:
            data = json.load(f)
        expenses = [Expense.from_dict(d) for d in data]
        # print(f"[DEBUG] Loaded {len(expenses)} expenses from {filename}")
        return expenses
    except FileNotFoundError:
        print(f"⚠️ No data file at {filename}; starting with 0 expenses.")
        return []
    except json.JSONDecodeError as e:
        # protect against corrupted JSON
        print(f"❌ Corrupted JSON at {filename}: {e}. Keeping file and starting empty.")
        return []



# used gpt 5 for the io/file handling since unfamiliar with how to exactly do it


# saving the monthly_budget


def save_budget(budget, filename="data/budget.json"):
    # Ensure the data folder exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Wrap in a dict to make it extendable later (you might add more info)
    data = {"monthly_budget": budget}

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Monthly budget saved successfully to '{filename}'")
 