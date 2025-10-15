# To be used for OOP and classes for cleaner structure:



from decimal import Decimal
from datetime import datetime

class Expense:
    def __init__(self, name: str, price: str, date: str, category: str = "misc"):
        # validate/normalize here
        self.name = name.strip()
        self.price = Decimal(price)  # precise for money
        self.date = self._parse_date(date)
        self.category = category.strip().lower()

    def _parse_date(self, date_str: str):
        """Validate & store date in YYYY-MM-DD format."""
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("❌ Date must be in YYYY-MM-DD format.")

    def to_dict(self) -> dict:
        """Convert Expense to a dict (for saving in JSON)."""
        return {
            "name": self.name,
            "price": str(self.price),       # JSON doesn’t support Decimal directly
            "date": self.date.isoformat(),  # "YYYY-MM-DD"
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Rebuild Expense object from a dict (when loading JSON)."""
        return cls(
            name=data["name"],
            price=data["price"],
            date=data["date"],
            category=data.get("category", "misc")
        )

    def __str__(self):
        # expense printing in command line
        return f"{self.name} | ${self.price} | {self.date} | {self.category}"
    

    