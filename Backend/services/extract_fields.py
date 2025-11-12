# Backend/services/extract_fields.py

import re
from datetime import datetime

def parse_expense_fields(ocr_text: str) -> dict:
    """
    Parse text extracted from OCR and identify key fields:
    - Date (supports numeric + written month formats)
    - Amount (prefers 'total' or highest value)
    - Item name (store/merchant name)
    - Category (keyword-based; defaults to 'Others')
    """

    # --- 1️⃣ Extract date (numeric and written formats) ---
    date_patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",     # 12/11/2025 or 12-11-25
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",       # 2025-11-12
        r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",  # 24 October 2025
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b", # October 24, 2025
        r"\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b",  # 24 Oct 2025
    ]
    date_match = None
    for pattern in date_patterns:
        match = re.search(pattern, ocr_text, flags=re.IGNORECASE)
        if match:
            date_match = match.group()
            break

    # --- 2️⃣ Extract all possible numeric amounts ---
    amounts = re.findall(r"\d+\.\d{2}", ocr_text)
    total_amount = None

    if amounts:
        # Look for a line containing 'total', 'amount due', etc.
        lines = ocr_text.splitlines()
        total_line_amounts = []
        for line in lines:
            if re.search(r"total|amount\s+due|grand\s+total|balance", line, flags=re.IGNORECASE):
                found = re.findall(r"\d+\.\d{2}", line)
                total_line_amounts.extend(found)
        if total_line_amounts:
            total_amount = max(map(float, total_line_amounts))
        else:
            # Fallback to the largest number in the whole receipt
            total_amount = max(map(float, amounts))

    amount = f"{total_amount:.2f}" if total_amount is not None else None

    # --- 3️⃣ Extract store / item name ---
    # Pick first line that looks like a merchant/store (alphabetic, not containing words like 'total' or 'receipt')
    lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
    possible_name = next(
        (line for line in lines if any(c.isalpha() for c in line)
         and not re.search(r"total|receipt|amount|invoice|order|date", line, flags=re.IGNORECASE)),
        None
    )

    # --- 4️⃣ Auto-categorize (keyword-based) ---
    category = guess_category(possible_name or "")

    return {
        "item_name": possible_name,
        "date": normalize_date(date_match),
        "amount": amount,
        "category": category,
    }


def normalize_date(date_str):
    """Convert various date string formats into DD-MM-YYYY (for frontend)."""
    if not date_str:
        return None

    # Remove extra spaces and unify separators
    date_str = date_str.strip().replace(" ", "").replace("/", "-")

    # Try common numeric formats (including 2-digit years)
    numeric_formats = ["%d-%m-%Y", "%d-%m-%y", "%Y-%m-%d", "%y-%m-%d"]
    for fmt in numeric_formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # Force 4-digit year in output
            return parsed.strftime("%d-%m-%Y")
        except ValueError:
            continue

    # Handle written month names (optional)
    month_map = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "jun": 6, "jul": 7, "aug": 8, "sep": 9,
        "oct": 10, "nov": 11, "dec": 12,
    }

    m1 = re.match(r"(\d{1,2})([A-Za-z]+)(\d{2,4})", date_str)
    if m1:
        day, month, year = m1.groups()
        if len(year) == 2:
            year = "20" + year
        month_num = month_map.get(month.lower(), 0)
        if month_num:
            return f"{int(day):02d}-{month_num:02d}-{year}"

    return None




def guess_category(text: str) -> str:
    """
    Basic keyword-based category guesser.
    Returns 'Others' if no match is found.
    """
    text = text.lower()
    categories = {
        "Food": [
            "restaurant", "cafe", "coffee", "starbucks", "burger", "dine",
            "supermarket", "grocery", "fairprice", "cold storage", "grocer",
            "prime", "sri selvi"
        ],
        "Transport": ["uber", "grab", "taxi", "bus", "mrt", "fuel", "petrol", "gojek", "trip"],
        "Clothes": ["mall", "store", "fashion", "clothing", "shop", "nike", "addidas"],
        "Entertainment": ["movie", "cinema", "netflix", "spotify"],
    }

    for cat, keywords in categories.items():
        if any(k in text for k in keywords):
            return cat
    return "Others"


# ---- Quick local test ----
#if __name__ == "__main__":
    sample_text = """
    Prime Supermarket
    Date: 05 November 2025
    Milk 2.50
    Eggs 4.80
    Chips 3.20
    TOTAL 10.50
    Thank you!
    """
    print(parse_expense_fields(sample_text))
