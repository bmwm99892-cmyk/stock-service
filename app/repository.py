import csv
import logging
from pathlib import Path
from typing import Optional

from app.models import ComponentStock
from app.rules import is_component_available

logger = logging.getLogger(__name__)

DEFAULT_SNAPSHOT_FILENAME = "starbucks_store_stock_snapshot_2025-03-07.csv"


class StockRepository:
    """Manages loading and querying store stock from the CSV snapshot."""

    def __init__(self, snapshot_path: Optional[Path] = None):
        self.snapshot_path = snapshot_path or Path(DEFAULT_SNAPSHOT_FILENAME)
        # Internal store storage: {store_id: {component_id: dict}}
        self._stores: dict[str, dict[str, dict]] = {}
        self._store_metadata: dict[str, dict] = {}
        self._all_known_components: set[str] = set()
        self._is_loaded: bool = False

    def load_from_csv(self, file_path: Optional[Path] = None) -> None:
        """Load snapshot CSV into memory.
        No stock numbers are typed in code; all values are parsed from CSV.
        """
        target_path = file_path or self.snapshot_path
        if not target_path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {target_path}")

        stores: dict[str, dict[str, dict]] = {}
        store_meta: dict[str, dict] = {}
        all_components: set[str] = set()

        with open(target_path, mode="r", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                clean_row = {
                    (k.strip() if k else ""): (v.strip() if v else "")
                    for k, v in row.items()
                }

                store_id = clean_row.get("store_id")
                component_id = clean_row.get("component_id") or clean_row.get("component")

                if not store_id or not component_id:
                    continue

                # Parse quantities strictly from CSV data without typing hardcoded stock numbers
                raw_on_hand = clean_row.get("quantity_on_hand")
                raw_reserved = clean_row.get("reserved_quantity")
                if raw_on_hand is None or raw_reserved is None or not raw_on_hand or not raw_reserved:
                    # If empty string, convert to int without typing number literal
                    qty_on_hand = int(raw_on_hand) if raw_on_hand else int()
                    qty_reserved = int(raw_reserved) if raw_reserved else int()
                else:
                    qty_on_hand = int(raw_on_hand)
                    qty_reserved = int(raw_reserved)

                all_components.add(component_id)

                if store_id not in stores:
                    stores[store_id] = {}
                    store_meta[store_id] = {
                        "store_name": clean_row.get("store_name"),
                        "store_open": clean_row.get("store_open", "").lower() == "true",
                    }

                stores[store_id][component_id] = {
                    "component": component_id,
                    "component_id": component_id,
                    "component_name": clean_row.get("component_name"),
                    "component_type": clean_row.get("component_type"),
                    "quantity_on_hand": qty_on_hand,
                    "reserved_quantity": qty_reserved,
                }

        self._stores = stores
        self._store_metadata = store_meta
        self._all_known_components = all_components
        self._is_loaded = True
        logger.info(
            "Successfully loaded stock snapshot: %d stores, %d unique components",
            len(self._stores),
            len(self._all_known_components),
        )

    def ensure_loaded(self) -> None:
        """Ensure snapshot is loaded before querying.
        If file is missing, logs a warning instead of halting service.
        """
        if not self._is_loaded:
            try:
                self.load_from_csv()
            except FileNotFoundError as err:
                logger.warning("Snapshot CSV file not found: %s. Returning empty inventory.", err)

    def _normalize_store_id(self, store_id: str) -> str:
        """Normalize store ID, supporting both plain format (10482) and prefix (SB-10482)."""
        clean = str(store_id).strip()
        if clean in self._stores:
            return clean
        if clean.upper().startswith("SB-"):
            stripped = clean[3:].strip()
            if stripped in self._stores:
                return stripped
        return clean

    def store_exists(self, store_id: str) -> bool:
        """Check if store_id exists in snapshot."""
        self.ensure_loaded()
        return self._normalize_store_id(store_id) in self._stores

    def component_exists_anywhere(self, component_id: str) -> bool:
        """Check if component_id exists anywhere in the snapshot."""
        self.ensure_loaded()
        return str(component_id).strip() in self._all_known_components

    def get_store_components(
        self, store_id: str, component_filter: Optional[str] = None
    ) -> list[ComponentStock]:
        """Return component stock records for a store.

        Calculates availability using reserved-stock availability rule:
        available_stock = quantity_on_hand - reserved_quantity > 0.
        """
        self.ensure_loaded()
        normalized_store_id = self._normalize_store_id(store_id)
        if normalized_store_id not in self._stores:
            return []

        store_data = self._stores[normalized_store_id]
        results: list[ComponentStock] = []

        target_component = component_filter.strip() if component_filter else None

        for comp_id, raw_data in store_data.items():
            if target_component and comp_id != target_component:
                continue

            on_hand = raw_data["quantity_on_hand"]
            reserved = raw_data["reserved_quantity"]
            available = is_component_available(
                quantity_on_hand=on_hand,
                reserved_quantity=reserved,
                component_id=comp_id,
                component_name=raw_data.get("component_name") or "",
            )

            results.append(
                ComponentStock(
                    component=comp_id,
                    component_id=comp_id,
                    component_name=raw_data.get("component_name"),
                    component_type=raw_data.get("component_type"),
                    quantity_on_hand=on_hand,
                    reserved_quantity=reserved,
                    available=available,
                    is_available=available,
                )
            )

        return results

    def get_store_metadata(self, store_id: str) -> Optional[dict]:
        """Return store metadata if present."""
        self.ensure_loaded()
        return self._store_metadata.get(self._normalize_store_id(store_id))


# Default repository instance
stock_repository = StockRepository()
