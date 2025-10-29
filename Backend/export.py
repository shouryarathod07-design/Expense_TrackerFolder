# backend/export.py
# Solely to be used for exporting Expenses to CSV files (and later TXT summaries, charts, etc.)
# Now supports safe appending to existing CSVs without duplicating entries.



"""
Saves expenses to CSV (append-safe).
Now ensures export always goes inside Expense_TrackerFolder/data/exports/.
"""

import csv
from pathlib import Path
from typing import List
from Expense_TrackerFolder.Backend.models import Expense


def export_to_csv(expenses: List[Expense], append: bool = True) -> Path:
    """
    Export a list of Expense objects to CSV.

    - Always saves to data/exports/expenses_export.csv
    - Creates folders if missing
    - If append=True, only adds new expenses not already in file
    """
    if not expenses:
        print("⚠️ No expenses to export.")
        return None

    # ✅ Build absolute, safe paths (no more random data folders)
    PROJECT_ROOT = Path(__file__).resolve().parents[1]  # → Expense_TrackerFolder
    EXPORTS_DIR = PROJECT_ROOT / "data" / "exports"
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = EXPORTS_DIR / "expenses_export.csv"

    headers = list(expenses[0].to_dict().keys())

    try:
        existing_ids = set()
        if append and file_path.exists():
            with file_path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "id" in row:
                        existing_ids.add(row["id"])

        mode = "a" if append and file_path.exists() else "w"
        with file_path.open(mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if mode == "w":
                writer.writeheader()

            new_rows = 0
            for exp in expenses:
                if exp.id not in existing_ids:
                    writer.writerow(exp.to_dict())
                    new_rows += 1

        print(
            f"✅ Export completed — {new_rows} new rows written "
            f"to '{file_path.name}' ({'appended' if mode == 'a' else 'created'})"
        )
        return file_path

    except Exception as e:
        print(f"❌ Failed to export expenses: {e}")
        return None
