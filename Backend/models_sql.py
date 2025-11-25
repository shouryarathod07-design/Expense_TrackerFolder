# Backend/models_sql.py
from datetime import date, datetime
import uuid

from sqlalchemy import (
    Column,
    String,
    Date,
    Numeric,
    Text,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from Backend.db import Base


class ExpenseDB(Base):
    __tablename__ = "expenses"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    expense_date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"ExpenseDB(id={self.id}, name={self.name}, "
            f"category={self.category}, price={self.price}, "
            f"expense_date={self.expense_date})"
        )
