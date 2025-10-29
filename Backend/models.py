from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from typing import Optional, Dict, Any, Union
import uuid


class Expense:
    """
    Core domain model for an expense entry.
    Represents a single transaction (e.g., food, travel, etc.).
    """

    def __init__(
        self,
        name: str,
        price: Union[str, float, Decimal],
        expense_date: Union[str, date],
        category: str,
        id: Optional[str] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name.strip().title()
        self.price = self._parse_price(price)
        self.expense_date = self._parse_date(expense_date)   # ✅ unified here
        self.category = category.strip().title()

    # ---------------------------
    # Validation / Parsing
    # ---------------------------
    @staticmethod
    def _parse_price(price) -> Decimal:
        try:
            value = Decimal(str(price))
            if value < 0:
                raise ValueError("Price must be non-negative.")
            return value.quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid price: {price}. {e}")

    @staticmethod
    def _parse_date(date_input) -> date:
        if isinstance(date_input, date):
            return date_input
        try:
            return datetime.strptime(date_input, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            raise ValueError(f"Invalid date: {date_input} (expected YYYY-MM-DD)")

    # ---------------------------
    # Serialization Helpers
    # ---------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "price": str(self.price),
            "expense_date": self.expense_date.isoformat(),   # ✅ unified key
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Expense":
        return cls(
            id=data.get("id"),
            name=data["name"],
            price=data["price"],
            expense_date=data.get("expense_date") or data.get("date"),  # ✅ backward compatible
            category=data["category"]
        )

    # ---------------------------
    # Representation
    # ---------------------------
    def __repr__(self) -> str:
        return (
            f"Expense(id={self.id}, name='{self.name}', "
            f"price=${self.price}, expense_date={self.expense_date}, category='{self.category}')"
        )

    def __str__(self) -> str:
        return f"{self.name} | ${self.price} | {self.category} | {self.expense_date}"
