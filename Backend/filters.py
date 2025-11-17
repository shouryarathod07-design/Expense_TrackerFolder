# backend/filters.py
# Solely to be used for search and filtering features for Expenses.
# This version is refactored to match the modular backend structure and includes fuzzy search for names.

from datetime import datetime, date
from typing import List, Optional
from decimal import Decimal
from fuzzywuzzy import fuzz    # external library for fuzzy name matching
from Backend.models import Expense


# ---------------------------------------------------------------
# Main Function: Search and Filter Expenses
# ---------------------------------------------------------------
def search_filter(
    expenses: List[Expense],
    name_query: Optional[str] = None,
    categories: Optional[List[str]] = None,
    date_query: Optional[str] = None,
    fuzzy_threshold: int = 65,  # how close the match should be (0–100)
) -> List[Expense]:
    """
    Filters expenses based on name, category, and date.
    Returns a list of matching Expense objects.
    """

    results = []

    # ------------------------------
    # Normalize Inputs (my style)
    # ------------------------------
    name_query = name_query.strip().lower() if name_query else ""
    categories = [c.lower().strip() for c in categories] if categories else []
    date_query = date_query.strip() if date_query else ""

    # ------------------------------
    # Parse date input safely
    # ------------------------------
    parsed_date = None
    date_parts = []
    if date_query:
        try:
            # Try to interpret full date first
            parsed_date = datetime.strptime(date_query, "%Y-%m-%d").date()
        except ValueError:
            # If not full date, maybe partial (e.g., 2025-10 or just 2025)
            date_parts = date_query.split("-")

    # --------------------------------------------------------------
    # Helper: fuzzy name matching
    # --------------------------------------------------------------
    # My style of small inline helper + short docstring
    def name_match(exp: Expense, query: str) -> bool:
        """Fuzzy matches expense name if query provided."""
        if not query:
            return True
        # fuzzy match (>= threshold) or substring check for loose match
        return fuzz.partial_ratio(exp.name.lower(), query) >= fuzzy_threshold or query in exp.name.lower()

    # --------------------------------------------------------------
    # Filtering Logic (same structure as your original)
    # --------------------------------------------------------------
    for e in expenses:
        # 1️⃣ Name check (with fuzzy)
        match_name = name_match(e, name_query)

        # 2️⃣ Category check
        if not categories:
            match_category = True
        else:
            match_category = e.category.lower() in categories

        # 3️⃣ Date check
        if not date_query:
            match_date = True
        else:
            try:
                if parsed_date:
                    # full exact date match (YYYY-MM-DD)
                    match_date = e.expense_date == parsed_date
                elif len(date_parts) == 1:
                    # match by year
                    match_date = e.expense_date.year == int(date_parts[0])
                elif len(date_parts) == 2:
                    # match by year and month
                    match_date = (
                        e.expense_date.year == int(date_parts[0])
                        and e.expense_date.month == int(date_parts[1])
                    )
                else:
                    match_date = True  # fallback
            except Exception:
                match_date = True

        # ----------------------------------------------------------
        # Append results if all match (as per my old pattern)
        # ----------------------------------------------------------
        if match_name and match_category and match_date:
            results.append(e)

    return results





