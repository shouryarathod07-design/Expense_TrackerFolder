# Expensr Backend

Expensr Backend is a FastAPI-based service that powers the Expensr personal expense tracker.  
It exposes a JSON REST API for creating, listing, and summarising expenses, and is used by both the CLI and the web frontend.

---

## Features

- Add new expenses with amount, category, description, and date (either manually or using OCR for reciept scanning)
- List all expenses, optionally filtered by date
- Monthly and per-category summary reports
- “Quick glance” indicators (e.g., total spend this month, top category)
- JSON-based persistence (easy to inspect and back up)
- Deployed to Render for production use

---

## Tech Stack

- **Language:** Python 3.x
- **Web Framework:** FastAPI
- **Data Validation:** Pydantic
- **Server:** Uvicorn (ASGI)
- **Persistence:** JSON file store (with `Decimal`-safe serialization)

---

## Architecture

The backend is structured in three layers:

1. **API Layer (FastAPI routes)**  
   Defines routes like `/expenses`, `/reports/summary`, and `/reports/quick`.  
   Uses Pydantic models to validate requests and shape responses.

2. **Domain / Service Layer (Tracker & reports)**  
   Encapsulates business logic, including:
   - Adding expenses
   - Generating monthly summaries
   - Computing quick-glance indicators

3. **Persistence Layer (JsonStore & models)**  
   Handles reading/writing expenses to a JSON file and converting between raw data and the `Expense` domain model.

This separation makes it easier to evolve the API, switch storage mechanisms, or reuse logic in other interfaces (e.g. CLI).

---

## Getting Started (Local Development)

### Prerequisites

- Python 3.9+ recommended
- `pip` or `pipenv` / `poetry` for dependency management

### Installation

```bash
git clone https://github.com/<your-username>/expensr-backend.git
cd expensr-backend

# Create and activate a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
