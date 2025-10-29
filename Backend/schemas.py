from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date
from typing import Optional
import uuid


class ExpenseBase(BaseModel):
    name: str = Field(..., example="Coffee")
    price: Decimal = Field(..., gt=0, example="4.50")
    expense_date: date = Field(..., example="2025-10-20")  # ✅ renamed
    category: str = Field(..., example="Food")

    class Config:
        orm_mode = True
        json_encoders = {Decimal: str}


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseRead(ExpenseBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()),
                    example="a13f9b9e-83a1-4ccf-9332-abc1234def56")

    class Config:
        orm_mode = True


class ExpenseUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    expense_date: Optional[date] = None  # ✅ match renamed field
    category: Optional[str] = None



# make notes:

