# Backend/crud.py
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from Backend.models_sql import ExpenseDB
from Backend.schemas import ExpenseCreate, ExpenseUpdate


# -----------------------------
# READ
# -----------------------------
async def get_expenses(session: AsyncSession) -> List[ExpenseDB]:
    result = await session.execute(
        select(ExpenseDB).order_by(ExpenseDB.expense_date.desc())
    )
    return list(result.scalars().all())


async def get_expense_by_id(
    session: AsyncSession, expense_id: str
) -> Optional[ExpenseDB]:
    result = await session.execute(
        select(ExpenseDB).where(ExpenseDB.id == expense_id)
    )
    return result.scalar_one_or_none()


# -----------------------------
# CREATE
# -----------------------------
async def create_expense(
    session: AsyncSession, expense_in: ExpenseCreate
) -> ExpenseDB:
    db_expense = ExpenseDB(
        name=expense_in.name.strip(),
        category=expense_in.category.strip(),
        price=expense_in.price,
        expense_date=expense_in.expense_date,
        note=expense_in.note,
    )
    session.add(db_expense)
    await session.commit()
    await session.refresh(db_expense)
    return db_expense


# -----------------------------
# UPDATE
# -----------------------------
async def update_expense(
    session: AsyncSession, expense_id: str, updates: ExpenseUpdate
) -> Optional[ExpenseDB]:
    db_expense = await get_expense_by_id(session, expense_id)
    if not db_expense:
        return None

    data = updates.dict(exclude_unset=True)

    if "name" in data:
        db_expense.name = data["name"].strip()
    if "category" in data:
        db_expense.category = data["category"].strip()
    if "price" in data:
        db_expense.price = data["price"]
    if "expense_date" in data:
        db_expense.expense_date = data["expense_date"]
    if "note" in data:
        db_expense.note = data["note"]

    await session.commit()
    await session.refresh(db_expense)
    return db_expense


# -----------------------------
# DELETE
# -----------------------------
async def delete_expense(
    session: AsyncSession, expense_id: str
) -> bool:
    db_expense = await get_expense_by_id(session, expense_id)
    if not db_expense:
        return False

    await session.delete(db_expense)
    await session.commit()
    return True
