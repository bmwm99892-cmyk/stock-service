"""Availability rules for store stock components.

Stock quantities are dynamically loaded from the snapshot; no fixed stock counts are hardcoded.
"""


def is_component_available(
    quantity_on_hand: int,
    reserved_quantity: int,
    component_id: str = "",
    component_name: str = "",
) -> bool:
    """Evaluate whether a store component is available.

    Availability rule: A milk is available when quantity_on_hand minus reserved_quantity is above 0, otherwise it is sold out.
    Reason: During the 7 a.m. rush, counting unfulfilled customer reservations prevents overselling and inaccurate promises.
    """
    # Rule: A milk is available when quantity_on_hand minus reserved_quantity is above 0, otherwise it is sold out.
    return (quantity_on_hand - reserved_quantity) > 0
