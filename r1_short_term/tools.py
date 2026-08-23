"""Rung 1 tools — one TODO stands between Iris and a real ticket."""

from google.adk.tools import ToolContext


def update_ticket(field: str, value: str, tool_context: ToolContext) -> dict:
    """Records one field of the support ticket.

    Args:
        field: Ticket field name in snake_case (order_number, product, symptom,
            refund_amount).
        value: The value the customer gave.

    Returns:
        dict with status and the field written.
    """
    key = f"ticket_{field}"
    # ── YOUR LINE ─ delete the "# TODO: " prefix ──────────────────────────
    # TODO: tool_context.state[key] = value
    return {"status": "success", "written": {key: value}}
