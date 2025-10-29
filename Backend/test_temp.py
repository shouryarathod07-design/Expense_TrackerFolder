"""
Quick verification script for storage.py
Run this once to confirm load/save behavior and data integrity.
Then delete it after verifying results.
"""

from Backend.storage import JsonStorage
from Backend.models import Expense
from decimal import Decimal
from datetime import date
import uuid
from pathlib import Path

# -------------------------------------------------------
# 1. Initialize storage and load existing data
# -------------------------------------------------------
storage = JsonStorage()
expenses = storage.load_expenses()
print(f"✅ Loaded {len(expenses)} expenses from file.")

# -------------------------------------------------------
# 2. Add a test expense
# -------------------------------------------------------
#new_expense = Expense(
 #   id=str(uuid.uuid4()),
  #  name="Test Lunch 3",
 #   price=Decimal("20.75"),
  #  expense_date=date.today(),
  #  category="food"
#)

#storage.add_expense(new_expense)
#print("✅ Added test expense successfully.")

# -------------------------------------------------------
# 3. Reload file to confirm persistence
# -------------------------------------------------------
reloaded_expenses = storage.load_expenses()
#found = any(e.id == new_expense.id for e in reloaded_expenses)
#print(f"🔍 Expense found after reload: {found}")

# -------------------------------------------------------
# 4. Test budget save/load
# -------------------------------------------------------
storage.save_budget(500.0)
budget = storage.load_budget()
print(f"✅ Budget read from file: {budget}")

# -------------------------------------------------------
# 5. Show final file paths for confirmation
# -------------------------------------------------------
from Backend.storage import EXPENSES_FILE, BACKUP_FILE, BUDGET_FILE
#print("\n🗂️  File locations:")
#print(f" - Expenses file: {EXPENSES_FILE}")
#print(f" - Backup file:   {BACKUP_FILE}")
#print(f" - Budget file:   {BUDGET_FILE}")

#print("\n✅ All tests executed successfully.")

# test for update and delete expense feature

target_id = storage.expenses[-1].id  # last added expense
#print("Editing:", target_id)

#storage.update_expense(target_id, price=Decimal("99.99"))
#storage.delete_expense(target_id)
#print("Updated + Deleted successfully.")

from Backend.storage import JsonStorage
from Backend.reports import monthly_summary, quick_indicator
from decimal import Decimal

store = JsonStorage()
expenses = store.load_expenses()

#print("Monthly summary:", monthly_summary(expenses))
#print("Quick indicator:", quick_indicator(expenses, 2025, 10, Decimal("500.00")))




# Test for my search and filter newly refactored version

from Backend.filters import search_filter
from Backend.storage import JsonStorage

#store = JsonStorage()
#expenses = store.load_expenses()

#results = search_filter(expenses, name_query="Meiki", categories=["Food"])

#print(f"\nFound {len(results)} results:")
#for e in results:
#    print(e)



# backend/--> export feature test
from Backend.models import Expense
from Backend.export import export_to_csv
from Backend.storage import JsonStorage
from pathlib import Path

#def test_export():
    # Load existing expenses from your JSON store
    #store = JsonStorage()
    #expenses = store.load_expenses()

    # Basic sanity check
    #print(f"Loaded {len(expenses)} expenses from JSON.")

    # Export to a test CSV file
    #output_path = Path("data/test_expenses_export.csv")
    #exported_file = export_to_csv(expenses, filename=str(output_path))

    # Check if file was created successfully
    #if exported_file and exported_file.exists():
     #   print(f"✅ CSV Export Test Passed! File saved at: {exported_file}")
    #else:
    #    print("❌ CSV Export Test Failed.")

#if __name__ == "__main__":
#    test_export()
  
  # backend/test_charts_temp.py
from Backend.storage import JsonStorage
from Backend.charts import monthly_spending_chart, monthly_spending_category_pie
from pathlib import Path

#def test_charts():
 #   store = JsonStorage()
  ## print(f"Loaded {len(expenses)} expenses from JSON.")

    # 1️⃣ Test monthly spending chart
    #chart1 = monthly_spending_chart(expenses, year=2025)
    #if chart1 and Path(chart1).exists():
     #   print(f"✅ Bar chart test passed: {chart1}")
    #else:
     #   print("❌ Bar chart test failed.")

    # 2️⃣ Test category pie chart
   # chart2 = monthly_spending_category_pie(expenses, year=2025, month=10)
    #if chart2 and Path(chart2).exists():
     #   print(f"✅ Pie chart test passed: {chart2}")
    #else:
     #   print("❌ Pie chart test failed.")

#if __name__ == "__main__":
 #   test_charts()
