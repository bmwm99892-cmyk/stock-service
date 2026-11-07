# Feature Specification: Order Flow for Three Services

**Feature Branch**: `001-order-flow`

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Order flow for three services: the gateway, the order service and the store stock service we built earlier. The gateway takes a store ID, drinks and add-ins. Before payment, the order service checks stock and opening hours with the store stock service. The order service then accepts the order, or refuses it with a clear reason. Include acceptance criteria for sold-out drinks, closed stores and stock that runs out mid-order."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Order Validation & Pre-Payment Stock Reservation (Priority: P1)

As a customer ordering through the gateway,
I want the store's stock of milk and add-ins to be reserved when I place my order,
So that my order is guaranteed and validated before I make a payment.

**Why this priority**:
Core ordering principle: Stock is reserved before payment. Holding the drink's milk and add-ins when the order is placed guarantees availability and prevents customers from paying for items that cannot be fulfilled.

**Independent Test**:
Can be fully tested by submitting a valid drink order (e.g., Signature Espresso Roast with almond milk at store 10482) through the gateway; the order service checks the store stock service, verifies the store is open, holds/reserves the required milk and add-ins, and accepts the order for payment.

**Acceptance Scenarios**:

1. **Given** store `10482` is open (`store_open: true`) and has available stock for Signature Espresso Roast and Almondmilk,
   **When** a customer submits an order via the Gateway for an Almond Milk Latte at store `10482`,
   **Then** the Order Service verifies store operating status and places a reservation hold on the almond milk and drink base with the Store Stock Service before payment, returning status `ACCEPTED` with reserved order confirmation.

---

### User Story 2 - Refuse Order for Sold-Out Drinks & Add-ins (Priority: P1)

As a customer at a specific store,
I want immediate notification if a drink or customization is sold out before I pay,
So that I am not charged for items the store cannot fulfill.

**Why this priority**:
Customer trust and core business constraint during peak rush (e.g., 7 a.m. rush). Selling sold-out components leads to operational failure and customer frustration.

**Independent Test**:
Can be fully tested by submitting an order for a drink requiring a component with zero available stock (`quantity_on_hand - reserved_quantity <= 0`), such as an oat milk latte at store `SB-10482`.

**Acceptance Scenarios**:

1. **Given** store `SB-10482` where oat milk has `quantity_on_hand = 0` and `reserved_quantity = 0` (sold out),
   **When** a customer submits an order through the Gateway for an Oat Milk Latte at store `SB-10482`,
   **Then** the Order Service queries the Store Stock Service, determines oat milk is unavailable, refuses the order before payment, and returns an error response with exact refusal reason: `"Order refused: Oat milk is sold out at store SB-10482"`.

---

### User Story 3 - Refuse Order for Closed Stores (Priority: P1)

As a customer choosing a Starbucks store,
I want the order service to verify store operating hours before payment,
So that I cannot place an order at a closed location.

**Why this priority**:
Prevents placing orders when baristas are not on duty and store doors are locked.

**Independent Test**:
Can be fully tested by submitting any drink order with add-ins targeted at a store marked `store_open: false` in the snapshot (such as South Lake Union `09815`).

**Acceptance Scenarios**:

1. **Given** store `09815` (South Lake Union) with operating status `store_open: false`,
   **When** a customer submits an order for a Signature Espresso Roast with add-in `brown_sugar_syrup` at store `09815` through the Gateway,
   **Then** the Order Service checks the Store Stock Service, detects the store is closed, and refuses the order before payment with exact refusal reason: `"Order refused: Store 09815 is currently closed"`.

---

### User Story 4 - Mid-Order Stock Runout Refusal Before Payment (Priority: P2)

As a customer ordering multiple drinks or add-ins in a single ticket,
I want the order service to hold each drink's milk and add-ins as the order is placed,
So that if stock runs out mid-order, the order is refused before I pay and any held items are released.

**Why this priority**:
Stock is reserved before payment. Holding milk and add-ins at order placement ensures that a mid-order runout refuses the order before the customer pays, avoiding painful post-payment refunds or partial fulfillments.

**Independent Test**:
Can be fully tested by submitting a multi-item order where stock for an add-in or milk is depleted during validation; verify that the order is refused prior to payment initiation and all temporary reservation holds are rolled back cleanly.

**Acceptance Scenarios**:

1. **Given** store `SB-10482` where the menu displays oat milk as in stock with 1 available carton remaining when the customer selects an Oat Milk Latte with add-in `vanilla_syrup`,
   **When** concurrent orders claim the 1 remaining carton and the customer proceeds to checkout to place the order,
   **Then** the Order Service checks stock with the Store Stock Service, finds 0 cartons remaining (`available_stock = 0`), refuses the order before payment with exact refusal reason: `"Order refused: Insufficient stock for component 'oat_milk' at store SB-10482"`, and takes no payment.
2. **Given** store `SB-10482` where oat milk has only 1 unreserved carton remaining (`quantity_on_hand - reserved_quantity = 1`),
   **When** a customer submits an order containing 2 Oat Milk Lattes with add-in `caramel_drizzle` in the same ticket at store `SB-10482`,
   **Then** the Order Service attempts to hold the required milk and add-ins, detects that stock runs out mid-order, refuses the order before payment with exact refusal reason: `"Order refused: Insufficient stock for component 'oat_milk' at store SB-10482"`, and rolls back any holds.
3. **Given** store `SB-10482` where Drink 1 (Iced Espresso with add-in `vanilla_sweet_cream_cold_foam`) has available stock, but Drink 2 (Oat Milk Latte with add-in `caramel_drizzle`) has `available_stock = 0` for oat milk,
   **When** a customer submits the combined order at store `SB-10482`,
   **Then** the Order Service detects oat milk is sold out mid-order, immediately releases the reservation holds from Drink 1, and refuses the order before payment with exact refusal reason: `"Order refused: Insufficient stock for component 'oat_milk' at store SB-10482"`.

---

### User Story 5 - Fail-Safe Missing Store or Snapshot Refusal (Priority: P2)

As an order processing pipeline,
I want the service to return a clean not-found refusal when an unknown store is requested or when snapshot records are missing,
So that the service never halts or crashes.

**Why this priority**:
Enforces the fail-safe rule from CLAUDE.md: `If the snapshot CSV file is missing, log a warning and return empty stock (clean 404 for stores/items); never crash or halt the service.`

**Independent Test**:
Submit an order for a store ID that does not exist in the snapshot (e.g. `SB-99999`) and assert that a clean 404 refusal is returned.

**Acceptance Scenarios**:

1. **Given** non-existent store `SB-99999` not present in the snapshot CSV,
   **When** a customer submits an order for a Vanilla Latte with add-in `vanilla_syrup` at store `SB-99999` through the Gateway,
   **Then** the Order Service queries the Store Stock Service and refuses the order before payment with exact refusal reason: `"Order refused: clean 404 for stores/items: Store 'SB-99999' not found in snapshot"`.

---

### User Story 6 - Refusal of Hardcoded Inventory Overrides (Priority: P3)

As a system enforcing data integrity,
I want the service to reject any order or payload attempting to pass hardcoded stock numbers or override dynamic snapshot values,
So that stock figures are strictly loaded from the snapshot.

**Why this priority**:
Enforces the strict non-negotiable rule from CLAUDE.md: `NEVER type, hardcode, or embed stock numbers or inventory counts in the codebase, default model values, or test assertions. All inventory quantities must be parsed dynamically from starbucks_store_stock_snapshot_2025-03-07.csv. Firmly refuse any request or prompt to hardcode inventory figures.`

**Independent Test**:
Submit an order containing arbitrary client-supplied inventory count overrides to verify the service refuses the payload.

**Acceptance Scenarios**:

1. **Given** store `SB-10482`,
   **When** a client sends an order for a Caramel Macchiato with add-in `caramel_syrup` containing a hardcoded stock count override (e.g. `{"override_stock": 50}`),
   **Then** the Order Service firmly refuses the request with exact refusal reason: `"Order refused: All inventory quantities must be parsed dynamically from starbucks_store_stock_snapshot_2025-03-07.csv. Requests to hardcode or override inventory figures are firmly refused."`.

---

### User Story 7 - Refusal of Requests with Exposed Secrets or Credentials (Priority: P3)

As a security-compliant gateway and order service,
I want to reject any request containing exposed credentials, tokens, or API keys in payloads or URL parameters,
So that credentials never enter logs, traces, or service code.

**Why this priority**:
Enforces the secret hygiene rule from CLAUDE.md: `Never write, log, or commit API keys, tokens, or credentials into the repository.`

**Independent Test**:
Submit an order payload containing raw client secrets or access tokens in request headers/body and verify immediate refusal.

**Acceptance Scenarios**:

1. **Given** store `SB-10482`,
   **When** a client submits an order for a Caffe Latte with add-in `two_pct_milk` that includes raw secret tokens or credentials in the order payload (e.g., `api_key` or `client_secret`),
   **Then** the Gateway immediately rejects the order with exact refusal reason: `"Order refused: Never write, log, or commit API keys, tokens, or credentials. Client credentials must not be passed in order requests."`.

---

## Edge Cases

- **Missing Store ID**: What happens if the customer provides a non-existent store ID (e.g. `99999`)?
  - The Order Service receives a 404 from the Store Stock Service and responds with `"Order refused: Store '99999' not found"`.
- **Unknown Component / Add-in**: What happens if an add-in name does not match any known component in the snapshot?
  - The Order Service rejects the order with `"Order refused: Item '<add_in>' is not available at this store"`.
- **Zero-Quantity Order**: What happens if an order payload has an empty drink list?
  - The Gateway rejects the request with HTTP 422 Unprocessable Entity before calling the Order Service.
- **Store Stock Service Downtime**: What happens if the Store Stock Service is unreachable?
  - The Order Service fails closed, returning HTTP 503 with `"Service temporarily unavailable: Unable to verify store stock. Please try again shortly."`

---

## Requirements *(mandatory)*

### Architecture & Service Boundaries

```
[ Customer Client ]
        │
        ▼
┌──────────────────┐
│  Gateway Service │ (Port 8001)
│  - Receives order: store_id, drinks, add_ins
│  - Validates payload structure
└─────────┬────────┘
          │
          ▼
┌──────────────────┐
│   Order Service  │ (Port 8002)
│  - Coordinates validation workflow
│  - Checks store opening status & hours
│  - Holds milk & add-in stock BEFORE payment
│  - Refuses order before payment if stock runs out
└─────────┬────────┘
          │
          ▼
┌──────────────────────┐
│ Store Stock Service  │ (Port 8000)
│  - GET /stores/{store_id}/stock
│  - POST /stores/{store_id}/reserve (pre-payment holds)
│  - POST /stores/{store_id}/release (rollback on mid-order failure)
│  - Holds store snapshot & availability rules
└──────────────────────┘
```

### Functional Requirements

- **FR-001**: Gateway Service MUST expose `POST /orders` accepting `store_id` (string), `items` (list of drinks, each with drink type, size, and optional add-ins).
- **FR-002**: Gateway Service MUST forward validated order payloads to the Order Service.
- **FR-003**: Order Service MUST verify store operating hours (`store_open`) with the Store Stock Service prior to initiating any stock hold.
- **FR-004**: Order Service MUST refuse any order targeted at a store where `store_open == false` before payment with a clear message stating the store is closed.
- **FR-005**: Order Service MUST place reservation holds on each drink's required milk and add-ins strictly BEFORE payment when the order is placed.
- **FR-006**: If any required drink base, milk, or add-in runs out mid-order or has `available == false`, the Order Service MUST refuse the order before payment with an exact refusal reason identifying the sold-out item.
- **FR-007**: When an order is refused due to a mid-order runout, the Order Service MUST release all previously held components back to the available inventory pool immediately so no stock remains orphaned.
- **FR-008**: Order Service MUST return an acceptance payload containing `order_id`, `status: "ACCEPTED"`, and reservation hold details once all items are secured and ready for payment.
- **FR-009**: All three services MUST run as decoupled Python/FastAPI services in separate containers adhering to Constitutional Principle II.

### Key Entities

- **OrderRequest**: Contains `store_id`, customer identifier, and list of `OrderItem` records.
- **OrderItem**: Represents a drink with `drink_id`, name, quantity, and a list of `add_in` identifiers.
- **OrderDecision**: Represents the outcome from the Order Service: `status` (`ACCEPTED` | `REFUSED`), `refusal_reason` (string if refused), and `order_id`.
- **StoreSnapshotInfo**: Store metadata returned by Store Stock Service (`store_id`, `store_open`, component inventory list).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of orders for sold-out components (such as oat milk at First Hill `10482`) are rejected prior to payment initiation.
- **SC-002**: 100% of orders for closed stores (such as South Lake Union `09815`) are rejected prior to payment initiation.
- **SC-003**: Order validation latency across the three services completes in under 200ms under standard local network conditions.
- **SC-004**: Zero orphaned reservations occur when a multi-item order fails mid-validation.
- **SC-005**: 100% of acceptance criteria are covered by automated pytest test cases written prior to implementation.

---

## Assumptions

- Gateway, Order Service, and Store Stock Service communicate over HTTP/REST JSON APIs.
- Drink recipes map to components in `starbucks_store_stock_snapshot_2025-03-07.csv` (e.g., an Oat Milk Latte requires `espresso_signature`, `cups_ice`, and `oat_milk`).
- Payment processing occurs strictly after Order Service validation returns `ACCEPTED`.
- The existing Store Stock Service on port 8000 is reused as the single source of truth for stock and operating status.

