# backend/reports.py
"""
All expense summaries and analytics (monthly, weekly, annual, etc.).
These functions are pure logic: they return data dictionaries or strings,
and never directly print to console. The CLI or API layer decides how to display it.
"""

from decimal import Decimal
from datetime import datetime, date, timedelta
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
from Expense_TrackerFolder.Backend.models import Expense


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def _group_monthly(expenses: List[Expense]) -> Dict[Tuple[int, int], Decimal]:
    """Group total expenses by (year, month)."""
    monthly_totals = defaultdict(Decimal)
    for e in expenses:
        monthly_totals[(e.expense_date.year, e.expense_date.month)] += e.price
    return monthly_totals


# ------------------------------------------------------------
# 1️⃣ Monthly Summary
# ------------------------------------------------------------
def monthly_summary(expenses: List[Expense]) -> Dict[Tuple[int, int], Decimal]:
    """Return total expenses grouped by (year, month)."""
    return _group_monthly(expenses)


# ------------------------------------------------------------
# 2️⃣ Monthly Summary by Category
# ------------------------------------------------------------
def monthly_summary_by_category(expenses: List[Expense]) -> Dict[Tuple[int, int], Dict[str, Decimal]]:
    """Return totals grouped by (year, month, category)."""
    monthly_cat_totals = defaultdict(lambda: defaultdict(Decimal))
    for e in expenses:
        monthly_cat_totals[(e.expense_date.year, e.expense_date.month)][e.category] += e.price
    return monthly_cat_totals


# ------------------------------------------------------------
# 3️⃣ Annual Summary
# ------------------------------------------------------------
def annual_summary(expenses: List[Expense]) -> Dict[int, Decimal]:
    """Return total expenses grouped by year."""
    annual_total = defaultdict(Decimal)
    for e in expenses:
        annual_total[e.expense_date.year] += e.price
    return dict(sorted(annual_total.items()))


# ------------------------------------------------------------
# 4️⃣ Weekly Summary
# ------------------------------------------------------------
def weekly_summary(expenses: List[Expense]) -> Dict[Tuple[int, int], Dict[str, object]]:
    """
    Return weekly totals with readable date ranges.
    {
        (year, week): {"total": Decimal, "start": date, "end": date}
    }
    """
    weekly_data = defaultdict(lambda: {"total": Decimal("0.00"), "start": None, "end": None})

    for e in expenses:
        year, week, weekday = e.expense_date.isocalendar()
        key = (year, week)
        weekly_data[key]["total"] += e.price

        if weekly_data[key]["start"] is None:
            start = e.expense_date - timedelta(days=weekday - 1)
            end = start + timedelta(days=6)
            weekly_data[key]["start"], weekly_data[key]["end"] = start, end

    return dict(sorted(weekly_data.items()))


# ------------------------------------------------------------
# 5️⃣ Average Daily Spending by Month
# ------------------------------------------------------------
def average_daily_spending_by_month(expenses: List[Expense]) -> Dict[Tuple[int, int], Dict[str, Decimal]]:
    """Return average daily spending per (year, month)."""
    monthly_data = defaultdict(list)
    for e in expenses:
        monthly_data[(e.expense_date.year, e.expense_date.month)].append(e)

    result = {}
    for key, exps in monthly_data.items():
        total = sum((e.price for e in exps), Decimal("0"))
        min_date, max_date = min(e.expense_date for e in exps), max(e.expense_date for e in exps)
        days = (max_date - min_date).days + 1
        avg = total / days if days else Decimal("0")
        result[key] = {"average": avg, "total": total, "days": days}
    return result


# ------------------------------------------------------------
# 6️⃣ Compare Monthly Summary vs Budget
# ------------------------------------------------------------
def monthly_summary_compare_budget(
    expenses: List[Expense], monthly_budget: Decimal
) -> Dict[Tuple[int, int], Dict[str, Decimal]]:
    """Compare each month's total spending with the budget."""
    summary = {}
    monthly_totals = _group_monthly(expenses)

    for (y, m), total in monthly_totals.items():
        diff = total - monthly_budget
        percent_over = (diff / monthly_budget) * 100 if monthly_budget else Decimal("0")
        summary[(y, m)] = {
            "total": total,
            "budget": monthly_budget,
            "diff": diff,
            "percent_over": percent_over,
        }
    return summary


# ------------------------------------------------------------
# 7️⃣ Quick Glance Reports
# ------------------------------------------------------------
def quick_indicator(expenses: List[Expense], year: int, month: int, monthly_budget: Decimal) -> str:
    """Indicator: total spent vs budget for given month."""
    monthly_totals = _group_monthly([e for e in expenses if e.expense_date.year == year and e.expense_date.month == month])
    if not monthly_totals:
        return "⚠️ No expenses found for that month."

    total = list(monthly_totals.values())[0]
    pct = (total / monthly_budget) * 100 if monthly_budget else Decimal("0")
    month_name = datetime(year, month, 1).strftime("%B")
    status = "✅ On track to stay under budget." if pct <= 100 else "⚠️ Over budget!"
    return f"{month_name} {year}: Spent ${total:.2f} of ${monthly_budget:.2f} budget ({pct:.1f}%) — {status}"


def quick_top_category(expenses: List[Expense], year: int, month: int) -> str:
    """Top spending category for a given month."""
    filtered = [e for e in expenses if e.expense_date.year == year and e.expense_date.month == month]
    if not filtered:
        return "⚠️ No expenses for this month."
    category_totals = defaultdict(Decimal)
    for e in filtered:
        category_totals[e.category] += e.price
    max_cat, max_val = max(category_totals.items(), key=lambda kv: kv[1])
    total = sum(category_totals.values())
    pct = (max_val / total) * 100 if total else Decimal("0")
    return f"{max_cat}: ${max_val:.2f} \n({pct:.1f}% of total expenses this month)"


def quick_month_over_month_change(expenses: List[Expense], year: int, month: int) -> str:
    """Compare spending between given month and previous month."""
    def total_for(y, m):
        return sum(e.price for e in expenses if e.expense_date.year == y and e.expense_date.month == m)

    current = total_for(year, month)
    prev = total_for(year, month - 1 if month > 1 else 12)
    if prev == 0:
        return "⚠️ Not enough data to compare."
    change = ((current - prev) / prev) * 100
    arrow = "📈" if change > 0 else "📉"
    return f"{arrow} Spending {'up' if change > 0 else 'down'} {abs(change):.1f}% from last month."


def quick_daily_burn_rate(expenses: List[Expense], year: int, month: int) -> str:
    """Average daily burn rate for given month."""
    filtered = [e for e in expenses if e.expense_date.year == year and e.expense_date.month == month]
    if not filtered:
        return "⚠️ No expenses to calculate daily burn rate."
    total = sum(e.price for e in filtered)
    min_d, max_d = min(e.expense_date for e in filtered), max(e.expense_date for e in filtered)
    days = (max_d - min_d).days + 1
    avg = total / days if days else Decimal("0")
    return f"🔥 {datetime(year, month, 1).strftime('%B %Y')}: ${avg:.2f}/day over {days} days (Total ${total:.2f})"
