# backend/filters.py
# Handles search + filtering logic for expenses, using RapidFuzz for fuzzy matching.

from datetime import datetime
from typing import List, Optional
from rapidfuzz import fuzz  # modern, fast fuzzy match library
from Backend.models import Expense


# ---------------------------------------------------------------
# Main Function: Search and Filter Expenses
# ---------------------------------------------------------------
def search_filter(
    expenses: List[Expense],
    name_query: Optional[str] = None,
    categories: Optional[List[str]] = None,
    date_query: Optional[str] = None,
    fuzzy_threshold: int = 65,
) -> List[Expense]:
    """
    Filters expenses by name, category, and date.
    Uses fuzzy matching for name search.
    """
    results = []

    # ------------------------------
    # Normalize inputs
    # ------------------------------
    name_query = name_query.strip().lower() if name_query else ""
    categories = [c.lower().strip() for c in categories] if categories else []
    date_query = date_query.strip() if date_query else ""

    # ------------------------------
    # Date parsing
    # ------------------------------
    parsed_date = None
    date_parts = []

    if date_query:
        try:
            parsed_date = datetime.strptime(date_query, "%Y-%m-%d").date()
        except ValueError:
            date_parts = date_query.split("-")

    # --------------------------------------------------------------
    # Fuzzy name matching helper (RapidFuzz)
    # --------------------------------------------------------------
    def name_match(exp: Expense, query: str) -> bool:
        if not query:
            return True

        exp_name = exp.name.lower()

        # RapidFuzz → correct order: (query, target)
        fuzzy_score = fuzz.partial_ratio(query, exp_name)

        # fuzzy OR direct substring match
        return fuzzy_score >= fuzzy_threshold or query in exp_name

    # --------------------------------------------------------------
    # Filtering logic
    # --------------------------------------------------------------
    for e in expenses:

        # 1️⃣ Name check
        match_name = name_match(e, name_query)

        # 2️⃣ Category check
        match_category = True
        if categories:
            match_category = e.category.lower() in categories

        # 3️⃣ Date check
        match_date = True
        if date_query:
            try:
                if parsed_date:
                    match_date = e.expense_date == parsed_date
                elif len(date_parts) == 1:
                    match_date = e.expense_date.year == int(date_parts[0])
                elif len(date_parts) == 2:
                    match_date = (
                        e.expense_date.year == int(date_parts[0])
                        and e.expense_date.month == int(date_parts[1])
                    )
            except Exception:
                match_date = True

        # Add only if all match
        if match_name and match_category and match_date:
            results.append(e)

    return results
