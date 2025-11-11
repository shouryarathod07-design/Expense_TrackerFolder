import csv
from pathlib import Path

def export_to_csv(expenses, append: bool = True):
    """Exports all expenses (including note) to a clean CSV file."""
    try:
        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)

        file_path = export_dir / "expenses_export.csv"
        mode = "a" if append and file_path.exists() else "w"

        with open(file_path, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "name",
                    "category",
                    "price",
                    "expense_date",
                    "note"
                ]
            )
            if f.tell() == 0:  # write header if new file
                writer.writeheader()

            for e in expenses:
                writer.writerow({
                    "id": e.id,
                    "name": e.name,
                    "category": e.category,
                    "price": float(e.price),
                    "expense_date": e.expense_date.isoformat(),
                    "note": e.note or ""
                })

        return file_path
    except Exception as e:
        print(f"[ERROR] CSV export failed: {e}")
        return None
