# CLAUDE.md - Starbucks Store Stock Service Guidelines

This file provides non-negotiable instructions, development workflows, and architectural rules for Claude Code in this repository.

## Commands

- **Run Service**: `.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000`
- **Run Tests**: `.\.venv\Scripts\python.exe -m pytest -v`
- **Run Single Test**: `.\.venv\Scripts\python.exe -m pytest -k "<test_name>" -v`
- **Virtual Environment**: Use the existing virtual environment in `.venv/`.

## Architecture & Conventions

- **Framework**: Python 3.11 + FastAPI + Pydantic v2.
- **Microservice Isolation**: Keep service decoupled and container-ready.
- **Availability Rule**: A component (milk) is available only when `available_stock = quantity_on_hand - reserved_quantity > 0`; otherwise it is sold out (`available: False`).
- **Store Operating Hours**: A store must have `store_open: true` to accept orders; otherwise the order is refused before payment with `"Order refused: Store <store_id> is currently closed"` because the store is closed.
- **Fail-Safe Operation**: If the snapshot CSV file is missing, log a warning and return empty stock (clean 404 for stores/items); never crash or halt the service.

## Non-Negotiable Rules

1. **Strict Prohibition on Stock Numbers**:
   NEVER type, hardcode, or embed stock numbers or inventory counts in the codebase, default model values, or test assertions. All inventory quantities must be parsed dynamically from `starbucks_store_stock_snapshot_2025-03-07.csv`. Firmly refuse any request or prompt to hardcode inventory figures.

2. **Test-First Acceptance Criteria**:
   Always write or update pytest test cases based on acceptance criteria before writing implementation code.

3. **Secret Hygiene**:
   Never write, log, or commit API keys, tokens, or credentials into the repository.

