from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ComponentStock(BaseModel):
    """Stock details for an individual component."""

    model_config = ConfigDict(populate_by_name=True)

    component: str = Field(description="Component identifier")
    component_id: str = Field(description="Snapshot component ID")
    component_name: Optional[str] = Field(default=None, description="Human readable component name")
    component_type: Optional[str] = Field(default=None, description="Component type category")
    quantity_on_hand: int = Field(description="Current quantity on hand loaded from snapshot")
    reserved_quantity: int = Field(description="Current reserved quantity loaded from snapshot")
    available: bool = Field(description="Whether component is currently available")
    is_available: bool = Field(description="Availability flag alias")


class StoreStockSummary(BaseModel):
    """Optional wrapper response if requested with store metadata."""

    store_id: str
    store_name: Optional[str] = None
    store_open: Optional[bool] = None
    components: list[ComponentStock]

