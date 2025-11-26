# Backend/schemas.py

from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date
from typing import Optional
import uuid


# ----------------------------------------------------
# Base schema (shared fields)
# ----------------------------------------------------
class ExpenseBase(BaseModel):
    name: str = Field(..., example="Coffee")
    price: Decimal = Field(..., gt=0, example="4.50")
    expense_date: date = Field(..., example="2025-10-20")
    category: str = Field(..., example="Food")
    note: Optional[str] = None

    class Config:
        orm_mode = True
        # Ensure Decimal is JSON-serializable
        json_encoders = {Decimal: lambda v: str(v)}


# ----------------------------------------------------
# CREATE schema (request body when creating)
# ----------------------------------------------------
class ExpenseCreate(ExpenseBase):
    """
    Inherits all fields from ExpenseBase.
    No 'id' here – the DB generates a UUID for us.
    """
    pass


# ----------------------------------------------------
# READ schema (response model)
# ----------------------------------------------------
class ExpenseRead(ExpenseBase):
    # IMPORTANT: use UUID type here to match DB model
    id: uuid.UUID = Field(
        ...,
        example="a13f9b9e-83a1-4ccf-9332-abc1234def56",
    )

    class Config(ExpenseBase.Config):
        pass


# ----------------------------------------------------
# UPDATE schema (partial updates)
# ----------------------------------------------------
class ExpenseUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    expense_date: Optional[date] = None
    category: Optional[str] = None
    note: Optional[str] = None

    class Config:
        orm_mode = True
        json_encoders = {Decimal: lambda v: str(v)}
