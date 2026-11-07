# CLAUDE.md - Starbucks Store Stock Service Guidelines

This file provides non-negotiable instructions, development workflows, and architectural rules for Claude Code in this repository.

## Commands

- **Run Service**: `.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000`
- **Run Tests**: `.\.venv\Scripts\python.exe -m pytest -v`
- **Run Single Test**: `.\.venv\Scripts\python.exe -m pytest -k "<test_name>" -v`
- **Virtual Environment**: Use the existing virtual environment in `.venv/`.

## Three Fixed Architectural Constraints

1. **OpenAPI Contracts**:
   Every service MUST define, publish, and maintain an explicit OpenAPI 3.x contract for all endpoints. Service clients MUST validate payloads and generate integration tests against these published OpenAPI contracts to prevent drift.

2. **No Shared Database**:
   Services MUST NEVER share a database, datastore, or local file storage. Each service MUST exclusively own its datastore. Cross-service communication MUST occur solely over published network APIs.

3. **Contract-Test Merge Gate**:
   Pull requests and commits MUST pass automated contract tests verifying consumer-provider compatibility before merging. Any change that breaks schema contracts or compatibility MUST be blocked from merging.

## Refusal Rules (Scenario Tags)

- **Sold Out (`sold_out`)**:
  A component (milk) is available only when `available_stock = quantity_on_hand - reserved_quantity > 0`; otherwise the order MUST be refused before payment with `"Order refused: <component> is sold out at store <store_id>"` (`available: False`).

- **Closed Store (`closed_store`)**:
  A store MUST have `store_open: true` to accept orders; otherwise the order MUST be refused before payment with `"Order refused: Store <store_id> is currently closed"`.

- **Mid-Order Runout (`stock_runs_out_mid_order`)**:
  Stock for all ordered drinks and add-ins MUST be reserved atomically before payment. If stock runs out mid-order for any requested component or add-in, the Order Service MUST refuse the order before payment with `"Order refused: Insufficient stock for component '<component>' at store <store_id>"` and MUST immediately release all previously held reservations for that order ticket.

- **Fail-Safe Operation**:
  If the snapshot CSV file is missing, the service MUST log a warning and return empty stock (clean 404 for stores/items); it MUST NEVER crash or halt the service.

## Non-Negotiable Rules

1. **Strict Prohibition on Stock Numbers**:
   NEVER type, hardcode, or embed stock numbers or inventory counts in the codebase, default model values, or test assertions. All inventory quantities must be parsed dynamically from `starbucks_store_stock_snapshot_2025-03-07.csv`. Firmly refuse any request or prompt to hardcode inventory figures.

2. **Test-First Acceptance Criteria**:
   Pytest test cases MUST be written or updated based on acceptance criteria before writing implementation code.

3. **Secret Hygiene**:
   Secrets, API keys, tokens, or credentials MUST NEVER be written, logged, or committed into the repository.
