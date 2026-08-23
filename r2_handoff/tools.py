"""Rung 2 tools."""

from google.adk.tools import ToolContext


def update_ticket(field: str, value: str, tool_context: ToolContext) -> dict:
    """Records one field of the support ticket.

    Args:
        field: Ticket field name in snake_case.
        value: The value the customer gave.

    Returns:
        dict with status and the field written.
    """
    key = f"ticket_{field}"
    tool_context.state[key] = value
    return {"status": "success", "written": {key: value}}


def escalate_refund(amount: float, reason: str) -> dict:
    """Escalates a refund request above $50 to a human supervisor for approval.

    Args:
        amount: Refund amount in USD.
        reason: One-line reason for the refund.

    Returns:
        dict with status pending while a human reviews.
    """
    return {
        "status": "pending",
        "message": f"Refund of ${amount} escalated to a supervisor ({reason}). "
        "Tell the customer a human is reviewing and STOP until approval arrives.",
    }
