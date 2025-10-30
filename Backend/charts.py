# Backend/charts.py
# Solely to be used for creating charts and visualizations for Expense data.
# Refactored for clean modular backend integration.

import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import json
from typing import List, Optional
from Expense_TrackerFolder.Backend.models import Expense


# --------------------------------------------------------------
# Helper: resolve the correct data/plots directory
# --------------------------------------------------------------
def _get_plot_dir() -> Path:
    """
    Returns the absolute path to the data/plots folder inside Expense_TrackerFolder.
    Automatically creates it if missing.
    """
    project_root = Path(__file__).resolve().parents[1]  # Expense_TrackerFolder
    plot_dir = project_root / "data" / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)
    return plot_dir


# --------------------------------------------------------------
# 1️⃣ Monthly Spending vs Budget Bar Chart
# --------------------------------------------------------------
def monthly_spending_chart(expenses: List[Expense], year: int, budget_file: str = None) -> Optional[Path]:
    """Generates a bar chart showing total monthly spending vs budget for a given year."""

    if not expenses:
        print("⚠️ No expenses available to plot.")
        return None

    # --- Aggregate totals by month ---
    monthly_totals = defaultdict(Decimal)
    for e in expenses:
        if e.expense_date.year == year:
            monthly_totals[e.expense_date.month] += e.price

    if not monthly_totals:
        print(f"⚠️ No expenses found for {year}.")
        return None

    # --- Prepare data for plotting ---
    months = sorted(monthly_totals.keys())
    totals = [monthly_totals[m] for m in months]
    month_labels = [datetime(year, m, 1).strftime("%b") for m in months]

    # --- Load monthly budget ---
    if budget_file is None:
        project_root = Path(__file__).resolve().parents[1]
        budget_file = project_root / "data" / "budget.json"

    try:
        with open(budget_file, "r", encoding="utf-8") as f:
            value = json.load(f)
            monthly_budget = Decimal(str(value["monthly_budget"]))
    except (FileNotFoundError, KeyError, ValueError):
        print("⚠️ Budget file missing or invalid, skipping budget line.")
        monthly_budget = None

    # --- Plot ---
    plt.figure(figsize=(10, 6))
    plt.bar(month_labels, totals, label="Actual Spending", color="#4CAF50", alpha=0.8)

    if monthly_budget is not None:
        plt.axhline(
            y=monthly_budget,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Budget (${monthly_budget})"
        )

    plt.title(f"Monthly Spending vs Budget — {year}")
    plt.xlabel("Month")
    plt.ylabel("Amount ($)")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()

    # --- Save chart ---
    output_dir = _get_plot_dir()
    output_path = output_dir / f"monthly_spending_{year}.png"

    try:
        plt.savefig(output_path)
        plt.close()
        print(f"✅ Chart saved successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error saving chart: {e}")
        return None


# --------------------------------------------------------------
# 2️⃣ Monthly Category Breakdown (Pie Chart)
# --------------------------------------------------------------
def monthly_spending_category_pie(
    expenses: List[Expense],
    year: int,
    month: int,
    threshold_percentage: float = 6.0
) -> Optional[Path]:
    """Creates a pie chart showing spending distribution by category for a given month/year."""

    monthly_cat_totals = defaultdict(lambda: defaultdict(Decimal))

    for e in expenses:
        if e.expense_date.year == year and e.expense_date.month == month:
            monthly_cat_totals[(year, month)][e.category] += e.price

    if not monthly_cat_totals:
        print(f"⚠️ No expenses recorded for {month}/{year}. Nothing to show.")
        return None

    # --- Prepare data ---
    pie_labels, pie_sizes = [], []
    for (y, m), categories in sorted(monthly_cat_totals.items()):
        for cat, total in sorted(categories.items()):
            pie_labels.append(cat)
            pie_sizes.append(float(total))

    total_spent = sum(pie_sizes)
    if total_spent == 0:
        print(f"⚠️ Total spending for {month}/{year} is 0.")
        return None

    # --- Merge small categories ---
    minor_total = 0
    merged_labels, merged_sizes = [], []
    for label, size in zip(pie_labels, pie_sizes):
        pct = (size / total_spent) * 100
        if pct < threshold_percentage:
            minor_total += size
        else:
            merged_labels.append(label)
            merged_sizes.append(size)
    if minor_total > 0:
        merged_labels.append(f"Minor Categories (<{threshold_percentage:.0f}%)")
        merged_sizes.append(minor_total)

    # --- Plot ---
    plt.figure(figsize=(8, 8))
    colors = list(plt.cm.tab20.colors[:len(merged_labels)])
    if "Minor Categories" in merged_labels[-1]:
        colors[-1] = "#d3d3d3"

    def autopct_with_values(pct):
        absolute = pct * total_spent / 100.0
        return f"${absolute:.0f}\n({pct:.1f}%)"

    plt.pie(
        merged_sizes,
        labels=merged_labels,
        colors=colors,
        autopct=autopct_with_values,
        startangle=90
    )

    plt.title(f"Category Distribution — {datetime(year, month, 1).strftime('%B %Y')}", y=1.10)
    plt.axis("equal")
    plt.legend(merged_labels, title="Categories", loc="center left", bbox_to_anchor=(-0.1, 0))

    # --- Save ---
    output_dir = _get_plot_dir()
    output_path = output_dir / f"category_breakdown_{year}_{month:02d}.png"

    try:
        plt.savefig(output_path)
        plt.close()
        print(f"✅ Pie chart saved successfully: {output_path}")
        return output_path
    except Exception as e:
        print(f"❌ Error saving pie chart: {e}")
        return None
