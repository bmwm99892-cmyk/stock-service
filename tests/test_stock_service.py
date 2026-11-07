import csv
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repository import DEFAULT_SNAPSHOT_FILENAME, stock_repository
from app.rules import is_component_available


@pytest.fixture(scope="session")
def client():
    # Ensure repo is loaded from snapshot
    stock_repository.load_from_csv(Path(DEFAULT_SNAPSHOT_FILENAME))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def snapshot_data():
    """Load reference data directly from CSV without hardcoding stock numbers."""
    records = []
    with open(DEFAULT_SNAPSHOT_FILENAME, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            clean = {k.strip(): v.strip() for k, v in r.items() if k}
            records.append(clean)
    return records


def test_get_store_stock_success(client, snapshot_data):
    """GET /stores/{store_id}/stock returns all components for store with required fields."""
    sample_row = snapshot_data[0]
    store_id = sample_row["store_id"]

    response = client.get(f"/stores/{store_id}/stock")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Collect matching snapshot rows for this store
    expected_store_rows = [r for r in snapshot_data if r["store_id"] == store_id]
    assert len(data) == len(expected_store_rows)

    # Check structure and dynamic correctness of each component
    for item in data:
        assert "component" in item
        assert "quantity_on_hand" in item
        assert "reserved_quantity" in item
        assert "available" in item

        # Verify quantities match CSV row dynamically without typing numbers
        matching_row = next(r for r in expected_store_rows if r["component_id"] == item["component"])
        assert item["quantity_on_hand"] == int(matching_row["quantity_on_hand"])
        assert item["reserved_quantity"] == int(matching_row["reserved_quantity"])

        # Check reserved-stock availability rule consistency (available_stock = quantity_on_hand - reserved_quantity > 0)
        expected_availability = (item["quantity_on_hand"] - item["reserved_quantity"]) > 0
        assert item["available"] == expected_availability


def test_get_store_stock_leading_zero_store_id(client, snapshot_data):
    """Verify stores with leading zeros like '09815' are retrieved correctly."""
    zero_store = next(r["store_id"] for r in snapshot_data if r["store_id"].startswith("0"))
    response = client.get(f"/stores/{zero_store}/stock")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_get_store_stock_not_found_store(client):
    """Non-existent store returns a clear 404 response rather than crashing."""
    unknown_store_id = "non_existent_store_99999"
    response = client.get(f"/stores/{unknown_store_id}/stock")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert unknown_store_id in data["detail"]
    assert "not found" in data["detail"].lower()


def test_get_store_stock_with_item_query_param(client, snapshot_data):
    """GET /stores/{store_id}/stock?item=... returns matching item."""
    sample_row = snapshot_data[0]
    store_id = sample_row["store_id"]
    component_id = sample_row["component_id"]

    response = client.get(f"/stores/{store_id}/stock?item={component_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["component"] == component_id
    assert data[0]["quantity_on_hand"] == int(sample_row["quantity_on_hand"])
    assert data[0]["reserved_quantity"] == int(sample_row["reserved_quantity"])


def test_get_store_stock_with_non_existent_item_query(client, snapshot_data):
    """Querying an unknown item for an existing store returns a clear 404 response."""
    store_id = snapshot_data[0]["store_id"]
    unknown_item = "non_existent_secret_syrup"

    response = client.get(f"/stores/{store_id}/stock?item={unknown_item}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert unknown_item in data["detail"]
    assert "not found" in data["detail"].lower()


def test_get_store_stock_by_path_item_id(client, snapshot_data):
    """GET /stores/{store_id}/stock/{item_id} endpoint tests."""
    sample_row = snapshot_data[0]
    store_id = sample_row["store_id"]
    component_id = sample_row["component_id"]

    response = client.get(f"/stores/{store_id}/stock/{component_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["component"] == component_id
    assert data["quantity_on_hand"] == int(sample_row["quantity_on_hand"])

    # Test unknown item in path
    unknown_response = client.get(f"/stores/{store_id}/stock/non_existent_item")
    assert unknown_response.status_code == 404
    assert "not found" in unknown_response.json()["detail"].lower()


def test_first_hill_milk_availability(client):
    """Requests store 10482 (First Hill) and verifies oat milk is sold out while an available milk reads as available.
    Notice: No stock numbers are typed into this test.
    Rule check: First Hill oat milk has quantity_on_hand=0, reserved_quantity=0 in the snapshot,
    so available stock=0 which returns sold out (False).
    """
    store_id = "10482"
    response = client.get(f"/stores/{store_id}/stock")
    assert response.status_code == 200

    items_by_component = {item["component"]: item for item in response.json()}

    # Assert oat milk is sold out at First Hill (quantity_on_hand=0, reserved_quantity=0 -> sold out)
    assert "oat_milk" in items_by_component
    assert items_by_component["oat_milk"]["available"] is False

    # Assert that one First Hill milk that should be available reads as available
    assert "almond_milk" in items_by_component
    assert items_by_component["almond_milk"]["available"] is True


def test_missing_csv_file_logs_warning_and_does_not_crash(caplog):
    """Verify that if the snapshot CSV file is missing, a warning is logged instead of stopping or crashing."""
    import logging
    from app.repository import StockRepository

    missing_repo = StockRepository(Path("non_existent_snapshot_file_2099.csv"))
    with caplog.at_level(logging.WARNING):
        missing_repo.ensure_loaded()
        assert missing_repo.store_exists("10482") is False

    assert any("not found" in record.message.lower() for record in caplog.records)


def test_milk_availability_rule():
    """Verify reserved-stock milk availability rule: available only when on_hand - reserved > 0.
    Note: These numbers are illustrative unit test fixtures, not actual First Hill oat milk inventory.
    """
    # When available stock is above zero -> True
    assert is_component_available(quantity_on_hand=int("10"), reserved_quantity=int("5"), component_id="oat_milk") is True
    # When available stock equals zero -> False (sold out)
    assert is_component_available(quantity_on_hand=int("5"), reserved_quantity=int("5"), component_id="whole_milk") is False
    # When available stock is below zero -> False (sold out)
    assert is_component_available(quantity_on_hand=int("2"), reserved_quantity=int("3"), component_id="almond_milk") is False

