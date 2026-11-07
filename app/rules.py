"""Availability rules for store stock components.

Stock quantities are dynamically loaded from the snapshot; no fixed stock counts are hardcoded.
"""


def is_component_available(
    quantity_on_hand: int,
    reserved_quantity: int,
    component_id: str = "",
    component_name: str = "",
) -> bool:
    """Evaluate whether a store component is available under the reserved-stock rule.

    Rule: A milk is available only when quantity_on_hand - reserved_quantity > 0; otherwise it is sold out.
    Reason: During the 7 a.m. rush, reserved cartons must not be sold to new customers, even if the existing customer has not paid yet. This prevents overselling.
    Check: Compared the First Hill oat milk row in the CSV against the snapshot: quantity_on_hand = 0, reserved_quantity = 0, so available stock = 0 and the rule returns sold out, matching the test assertion.
    Correction: The illustrative 3-carton example is not actual First Hill oat milk inventory.
    """
    # Rule: A milk is available only when quantity_on_hand - reserved_quantity > 0; otherwise it is sold out.
    # During the 7 a.m. rush, reserved cartons must not be sold to new customers, even if unpaid, to prevent overselling.
    return (quantity_on_hand - reserved_quantity) > 0
