# Backend/migrate_json_to_postgres.py

import asyncio
from decimal import Decimal
import uuid

from Backend.storage import JsonStorage
from Backend.models_sql import ExpenseDB
from Backend.db import AsyncSessionLocal
from Backend.models import Expense  # domain model


async def migrate_json_to_postgres():
    print("🚀 Starting migration from JSON → PostgreSQL...\n")

    # Load JSON expenses
    json_store = JsonStorage()
    json_expenses = json_store.load_expenses()

    if not json_expenses:
        print("⚠️ No JSON expenses found. Exiting.")
        return

    print(f"📦 Found {len(json_expenses)} expenses in JSON.")
    print("⏳ Migrating...\n")

    migrated = 0
    skipped = 0

    async with AsyncSessionLocal() as session:
        for exp in json_expenses:

            # Skip if ID already exists in DB
            existing = await session.get(ExpenseDB, exp.id)
            if existing:
                skipped += 1
                continue

            # Convert to DB model
            db_expense = ExpenseDB(
                id=uuid.UUID(str(exp.id)),
                name=exp.name,
                category=exp.category,
                price=Decimal(str(exp.price)),
                expense_date=exp.expense_date,
                note=exp.note,
            )

            session.add(db_expense)
            migrated += 1

        await session.commit()

    print("✅ Migration complete!")
    print(f"🟢 Migrated: {migrated}")
    print(f"🟡 Skipped (already in DB): {skipped}")
    print("\n🎉 All done!")


if __name__ == "__main__":
    asyncio.run(migrate_json_to_postgres())
