import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, status

from app.models import ComponentStock
from app.repository import stock_repository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager that loads stock snapshot on application startup."""
    try:
        stock_repository.load_from_csv()
    except FileNotFoundError as err:
        # Avoid crashing or stopping the service if CSV is missing; log a warning instead
        logger.warning(
            "Warning on startup: Stock snapshot file was not found (%s). Service is running with empty stock.",
            err,
        )
    yield


app = FastAPI(
    title="Starbucks Store Stock Service",
    description="FastAPI service providing real-time store component stock levels and availability.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get(
    "/stores/{store_id}/stock",
    response_model=list[ComponentStock],
    summary="Get stock levels and availability for store components",
    description=(
        "Returns each component for the given store with quantity_on_hand, "
        "reserved_quantity, and availability. Returns 404 if the store or item is not found."
    ),
    responses={
        404: {
            "description": "Store or component item not found in snapshot",
            "content": {
                "application/json": {
                    "example": {"detail": "Store '99999' not found in snapshot"}
                }
            },
        }
    },
)
def get_store_stock(
    store_id: str,
    component: Optional[str] = Query(
        default=None,
        alias="item",
        description="Optional component or item identifier to filter by",
    ),
) -> list[ComponentStock]:
    """Retrieve stock levels for a store's components.

    - Returns clear 404 if store is not in snapshot.
    - Returns clear 404 if requested item/component is not in snapshot.
    """
    normalized_store_id = store_id.strip()

    # Verify store exists in snapshot
    if not stock_repository.store_exists(normalized_store_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store '{normalized_store_id}' not found in snapshot",
        )

    # If specific component/item was requested via query parameter
    if component:
        cleaned_component = component.strip()
        items = stock_repository.get_store_components(
            normalized_store_id, component_filter=cleaned_component
        )
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item '{cleaned_component}' not found in snapshot for store '{normalized_store_id}'",
            )
        return items

    # Return all components for that store
    components = stock_repository.get_store_components(normalized_store_id)
    if not components:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No stock items found for store '{normalized_store_id}' in snapshot",
        )

    return components


@app.get(
    "/stores/{store_id}/stock/{item_id}",
    response_model=ComponentStock,
    summary="Get stock for a specific component in a store",
    description="Convenience path endpoint to query an individual item's stock.",
    responses={
        404: {
            "description": "Store or item not found in snapshot",
            "content": {
                "application/json": {
                    "example": {"detail": "Item 'unknown_item' not found in snapshot for store '10482'"}
                }
            },
        }
    },
)
def get_store_item_stock(store_id: str, item_id: str) -> ComponentStock:
    """Retrieve stock for a single component by item_id in path."""
    normalized_store_id = store_id.strip()
    normalized_item_id = item_id.strip()

    if not stock_repository.store_exists(normalized_store_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store '{normalized_store_id}' not found in snapshot",
        )

    items = stock_repository.get_store_components(
        normalized_store_id, component_filter=normalized_item_id
    )
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item '{normalized_item_id}' not found in snapshot for store '{normalized_store_id}'",
        )

    return items[0]

