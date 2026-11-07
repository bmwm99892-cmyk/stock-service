# Starbucks Store Stock Service

A FastAPI microservice that loads Starbucks store stock from `starbucks_store_stock_snapshot_2025-03-07.csv` and exposes real-time stock levels and component availability.

## Availability Rule
> **Rule**: `available_stock = quantity_on_hand - reserved_quantity`. A milk is available only when `available_stock > 0`; otherwise it is sold out.
> **Reason**: Reserved cartons must be excluded from stock available to new customers during the 7 a.m. rush, even if they have not been paid for yet, to prevent overselling.
> **First Hill Snapshot Check**: Store ID `10482`, oat milk: `quantity_on_hand` = 0, `reserved_quantity` = 0, `available_stock` = 0 $\rightarrow$ sold out (`available: False`). Note: The illustrative 3-carton example is test data, not actual First Hill inventory.

## Setup & Virtual Environment

Dependencies (`fastapi`, `uvicorn`, `pytest`, `httpx`) are installed inside `.venv`.

To activate the virtual environment:
```powershell
.\.venv\Scripts\Activate.ps1
```

## Running the Service

Start the FastAPI application with Uvicorn:
```powershell
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Get Store Stock
- **Route**: `GET /stores/{store_id}/stock`
- **Optional Query Parameter**: `?item=<component_id>`
- **Response**:
  ```json
  [
    {
      "component": "oat_milk",
      "component_id": "oat_milk",
      "component_name": "Oatmilk",
      "component_type": "drink_base",
      "quantity_on_hand": 72,
      "reserved_quantity": 0,
      "available": true,
      "is_available": true
    }
  ]
  ```
- **Not Found (404)**: If store or item is not in snapshot:
  ```json
  {
    "detail": "Store '99999' not found in snapshot"
  }
  ```

### 2. Get Single Item Stock
- **Route**: `GET /stores/{store_id}/stock/{item_id}`

## Running Tests

Run pytest with:
```powershell
.\.venv\Scripts\pytest -v
```

