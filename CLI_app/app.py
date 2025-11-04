# CLI_app/app.py
"""
Main CLI entry point for the Expense Tracker project.
"""

import sys, os, json
from decimal import Decimal
from datetime import date,datetime
from pathlib import Path
from typing import List
import csv


# Ensure the project root (the parent of Expense_TrackerFolder) is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Imports ---
from Expense_TrackerFolder.Backend.storage import JsonStorage
from Expense_TrackerFolder.Backend.models import Expense
from Expense_TrackerFolder.Backend.export import export_to_csv
from Expense_TrackerFolder.Backend.filters import search_filter
from Expense_TrackerFolder.Backend.charts import monthly_spending_chart, monthly_spending_category_pie
from Expense_TrackerFolder.Backend.reports import (
    monthly_summary_compare_budget,
    monthly_summary_by_category,
    weekly_summary,
    annual_summary,
    average_daily_spending_by_month,
    quick_indicator,
    quick_daily_burn_rate,
    quick_month_over_month_change,
    quick_top_category
)


# --- Helpers ---
def show_categories():
    categories = ["Food", "Travel", "Ent", "Misc", "Clothing", "Others"]
    print("\nSelect a category:")
    for i, c in enumerate(categories, start=1):
        print(f"{i}. {c}")
    return categories

# --- Handlers ---
def handle_view_expenses(expenses, store):
    if not expenses:
        print("No expenses recorded.")
    else:
        print("\nExpenses List:")
        for i, e in enumerate(expenses, start=1):
            print(f"{i}. {e}")

def handle_add_expense(expenses, store):
    name = input("Name: ").strip()
    try:
        price = Decimal(input("Price: ").strip())
    except Exception:
        print("Invalid price format.")
        return

    date_input = input("Date (YYYY-MM-DD): ").strip()
    categories = show_categories()
    cat_choice = input("Category (1-6): ").strip()
    category = (
        categories[int(cat_choice) - 1]
        if cat_choice.isdigit() and 1 <= int(cat_choice) <= len(categories)
        else "Misc"
    )

    expense = Expense(name, price, date_input, category)
    expenses.append(expense)
    store.save_expenses(expenses)
    print("✅ Expense added successfully!")



def handle_delete_expense(expenses, store):
    """Delete an expense by selecting its index."""
    if not expenses:
        print("⚠️ No expenses available to delete.")
        return

    print("\nExpenses List:")
    for i, e in enumerate(expenses, start=1):
        print(f"{i}. {e}")

    try:
        choice = int(input("\nEnter the number of the expense to delete: ").strip())
        if 1 <= choice <= len(expenses):
            expense_to_delete = expenses[choice - 1]
            confirm = input(f"Are you sure you want to delete '{expense_to_delete.name}'? (y/n): ").strip().lower()
            if confirm == "y":
                store.delete_expense(expense_to_delete.id)
                expenses[:] = store.load_expenses()  # refresh in-memory list
                print("✅ Expense deleted successfully.")
            else:
                print("❌ Deletion cancelled.")
        else:
            print("⚠️ Invalid expense number.")
    except ValueError:
        print("❌ Please enter a valid number.")


def handle_set_budget(store):
    """Set or update the user's monthly budget."""
    try:
        budget = float(input("\nEnter your monthly budget ($): ").strip())
        if budget <= 0:
            print("⚠️ Budget must be greater than 0.")
            return
        store.save_budget(budget)
        print(f"✅ Monthly budget set to ${budget:.2f}")
    except ValueError:
        print("❌ Invalid input. Please enter a numeric value.")


def handle_view_budget(store):
    """View the current saved monthly budget."""
    budget = store.load_budget()
    if budget:
        print(f"\n💰 Current Monthly Budget: ${budget:.2f}")
    else:
        print("⚠️ No monthly budget set yet.")


def handle_search_filter(expenses, store):
    print("\n🔍 Search & Filter Options")

    name_query = input("Enter name to search (or leave blank): ").strip().lower()
    
    # Category choices
    categories = ["Food", "Travel", "Ent", "Misc", "Clothing", "Others"]
    print("\nAvailable categories:")
    for i, c in enumerate(categories, 1):
        print(f"{i}. {c}")
    
    category_choice = input("Enter category numbers (comma-separated, or leave blank): ").strip()
    selected_categories = [
        categories[int(i) - 1].lower()
        for i in category_choice.split(",") if i.strip().isdigit() and 1 <= int(i) <= len(categories)
    ] if category_choice else []

    # Date filter
    date_query = input("Enter date (YYYY-MM-DD, YYYY-MM, or YYYY) to filter (or leave blank): ").strip()

    # Run the search
    results = search_filter(expenses, name_query, selected_categories, date_query)

    # Display results
    if not results:
        print("\n❌ No matching expenses found.")
    else:
        print("\n✅ Matching Expenses:")
        for i, e in enumerate(results, 1):
            print(f"{i}. {e}")



from decimal import Decimal
from pprint import pprint  # nice formatting for dicts

def handle_reports(expenses, store):
    if not expenses:
        print("⚠️ No expenses found to summarize.")
        return

    print("\n📈 Reports Menu:")
    print("1. Monthly Summary (vs Budget)")
    print("2. Monthly Summary by Category")
    print("3. Weekly Summary")
    print("4. Annual Summary")
    print("5. Average Daily Spending")
    choice = input("Select report type (1–5): ").strip()

    # --- Option 1: Monthly Summary vs Budget ---
    if choice == "1":
        monthly_budget = Decimal(str(store.load_budget()))
        result = monthly_summary_compare_budget(expenses, monthly_budget)
        print("\n📊 Monthly Summary vs Budget:")
        for (y, m), data in result.items():
            month_name = datetime(y, m, 1).strftime("%B")
            print(f"→ {month_name} {y}: ${data['total']:.2f} (Budget ${data['budget']:.2f}) "
                  f"→ {data['percent_over']:.2f}% {'over' if data['diff']>0 else 'under'} budget")

    # --- Option 2: Monthly Summary by Category ---
    elif choice == "2":
        result = monthly_summary_by_category(expenses)
        print("\n📊 Monthly Summary by Category:")
        for (y, m), cats in result.items():
            month_name = datetime(y, m, 1).strftime("%B")
            print(f"\n🗓️ {month_name} {y}:")
            for cat, total in cats.items():
                print(f"   {cat:<12} ${total:.2f}")

    # --- Option 3: Weekly Summary ---
    elif choice == "3":
        result = weekly_summary(expenses)
        print("\n📅 Weekly Summary:")
        for (y, w), info in result.items():
            print(f"Week {w} ({info['start']} → {info['end']}): ${info['total']:.2f}")

    # --- Option 4: Annual Summary ---
    elif choice == "4":
        result = annual_summary(expenses)
        print("\n📆 Annual Summary:")
        for year, total in result.items():
            print(f"{year}: ${total:.2f}")

    # --- Option 5: Average Daily Spending ---
    elif choice == "5":
        result = average_daily_spending_by_month(expenses)
        print("\n🔥 Average Daily Spending by Month:")
        for (y, m), data in result.items():
            month_name = datetime(y, m, 1).strftime("%B")
            print(f"{month_name} {y}: ${data['average']:.2f}/day over {data['days']} days (Total ${data['total']:.2f})")

    else:
        print("❌ Invalid choice.")

    input("\nPress Enter to return to main menu...")

# ----QUICK INSIGHTS (Personal favourite*)-----

def handle_quick_insights(expenses, store):
    """Show quick-glance insights for a specific month/year."""
    if not expenses:
        print("⚠️ No expenses found to analyze.")
        return

    try:
        year = int(input("Enter year (e.g. 2025): ").strip())
        month = int(input("Enter month (1–12): ").strip())
    except ValueError:
        print("❌ Invalid input; please enter numbers for year and month.")
        return

    monthly_budget = Decimal(str(store.load_budget()))

    print("\n📊 QUICK GLANCE REPORTS")
    print("-" * 40)
    print(quick_indicator(expenses, year, month, monthly_budget))
    print(quick_top_category(expenses, year, month))
    print(quick_month_over_month_change(expenses, year, month))
    print(quick_daily_burn_rate(expenses, year, month))

    # optional: export to text
    
    

    export = input("\nWould you like to export this report to text file? (y/n): ").strip().lower()
    if export == "y":
        lines = [
            quick_indicator(expenses, year, month, monthly_budget),
            quick_top_category(expenses, year, month),
            quick_month_over_month_change(expenses, year, month),
            quick_daily_burn_rate(expenses, year, month),
        ]

        # ✅ Determine absolute path to project root
        PROJECT_ROOT = Path(__file__).resolve().parents[1]  # goes up from CLI_app → Expense_TrackerFolder
        DATA_DIR = PROJECT_ROOT / "data"
        REPORTS_DIR = DATA_DIR / "reports"

        # ✅ Ensure folders exist
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        # ✅ Build output file path inside correct folder
        path = REPORTS_DIR / f"Quick_Glance_Report_{year}_{month:02d}.txt"

        # ✅ Write (overwrite if exists)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"✅ Report saved successfully to: {path}")


# export csv handler--)

def handle_export_to_csv(expenses, store):
    """Export all expenses to CSV."""
    if not expenses:
        print("⚠️ No expenses recorded to export.")
        return

    confirm = input("Export all expenses to CSV? (y/n): ").strip().lower()
    if confirm == "y":
        export_to_csv(expenses)
    else:
        print("❌ Export canceled.")


# charts handler

def handle_charts(expenses, store):
    """Generate visual charts for expenses."""
    if not expenses:
        print("⚠️ No expenses to visualize.")
        return

    print("\n=== Chart Options ===")
    print("1. Monthly Spending vs Budget (Bar Chart)")
    print("2. Monthly Category Breakdown (Pie Chart)")

    choice = input("Select an option (1-2): ").strip()
    if choice == "1":
        try:
            year = int(input("Enter year (e.g., 2025): ").strip())

            # ✅ Use correct project path for budget file
            PROJECT_ROOT = Path(__file__).resolve().parents[1]
            budget_file = PROJECT_ROOT / "data" / "budget.json"

            monthly_spending_chart(expenses, year, str(budget_file))
        except ValueError:
            print("❌ Invalid year format.")
    elif choice == "2":
        try:
            year = int(input("Enter year (e.g., 2025): ").strip())
            month = int(input("Enter month number (1-12): ").strip())
            monthly_spending_category_pie(expenses, year, month)
        except ValueError:
            print("❌ Invalid input for year/month.")
    else:
        print("❌ Invalid chart option.")



# --- CLI Loop ---
def main():
    store = JsonStorage()
    expenses = store.load_expenses()
    print(f"✅ Loaded {len(expenses)} expenses.\n")

    menu = {
        "1": ("View Expenses", handle_view_expenses),
        "2": ("Add Expense", handle_add_expense),  
        "3": ("Delete Expense", handle_delete_expense),
        "4": ("Set Monthly Budget", lambda e, s: handle_set_budget(s)),
        "5": ("View Monthly Budget", lambda e, s: handle_view_budget(s)),
        "6": ("Search & Filter",handle_search_filter),
        "7": ("Reports", handle_reports),
        "8": ("Quick Insights (Glance)",handle_quick_insights),
        "9":  ("Export to csv",handle_export_to_csv),
        "10":("Charts & Graphs",handle_charts)
    }

    while True:
        print("\n=== Expense Tracker Menu ===")
        for k, (desc, _) in menu.items():
            print(f"{k}. {desc}")
        print("X. Exit")

        choice = input("Select an option: ").strip().lower()
        if choice in menu:
            _, func = menu[choice]
            func(expenses, store)
        elif choice in ("x", "exit"):
            store.save_expenses(expenses)
            print("👋 Goodbye! Data saved.")
            break
        else:
            print("❌ Invalid option, please try again.")

if __name__ == "__main__":
    main()








