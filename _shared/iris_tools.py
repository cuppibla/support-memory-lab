"""Iris's tools. Each rung's agent picks the subset it has earned.

Verified on google-adk 2.7.1 (Phase-0, 2026-08-22). Every tool degrades
gracefully when its backing service isn't wired — a missing backend should
never crash a turn.
"""

from google.adk.tools import ToolContext

from . import store


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


async def close_ticket(resolution: str, tool_context: ToolContext) -> dict:
    """Closes the ticket and files this conversation to long-term memory.

    Args:
        resolution: One-line description of how the issue was resolved.

    Returns:
        dict with status and whether the conversation was filed to memory.
    """
    tool_context.state["ticket_status"] = f"closed: {resolution}"
    inv = getattr(tool_context, "_invocation_context", None)
    memory_service = getattr(inv, "memory_service", None) if inv else None
    session = getattr(inv, "session", None) if inv else None
    if memory_service is None or session is None:
        return {"status": "closed_without_memory",
                "note": "no memory service wired on this runner"}
    await memory_service.add_session_to_memory(session)
    return {"status": "success", "filed_to_memory": True, "resolution": resolution}


async def recall_history(query: str, tool_context: ToolContext) -> dict:
    """Searches this customer's past support conversations.

    Args:
        query: What to look for in past conversations.

    Returns:
        dict with any past facts found.
    """
    try:
        result = await tool_context.search_memory(query)
    except ValueError as e:  # no memory service on this runner — degrade, don't crash
        return {"status": "empty", "past_conversations": [], "note": str(e)}
    memories = []
    for m in getattr(result, "memories", []) or []:
        content = getattr(m, "content", None)
        if content and content.parts:
            memories.extend(p.text for p in content.parts if getattr(p, "text", None))
    return {"status": "success", "past_conversations": memories[:10]}


def record_damage(model: str, damage: str, batch: str, tool_context: ToolContext) -> dict:
    """Records what a product photo shows: model, visible damage, and batch code.

    Args:
        model: Product model name visible in the photo.
        damage: Short description of the visible damage.
        batch: Batch code printed on the product (e.g. B7); "unknown" if not visible.

    Returns:
        dict with status and the recorded facts.
    """
    tool_context.state["photo_model"] = model
    tool_context.state["photo_damage"] = damage
    tool_context.state["photo_batch"] = batch
    return {"status": "success",
            "recorded": {"model": model, "damage": damage, "batch": batch}}


def search_tickets(text: str) -> dict:
    """Searches ALL support tickets by text similarity.

    Args:
        text: Words to search for in past ticket text.

    Returns:
        dict with matching tickets from any customer or product.
    """
    words = [w[:5] for w in text.lower().split() if len(w) >= 3]
    if not words:
        return {"status": "success", "match_count": 0, "matches": []}
    clause = " OR ".join("t.text LIKE ?" for _ in words)
    db = store.conn()
    rows = db.execute(
        "SELECT t.id, p.name, t.text FROM tickets t "
        "JOIN orders o ON t.order_id=o.id LEFT JOIN products p ON p.id=o.product_id "
        f"WHERE {clause} ORDER BY t.id DESC", [f"%{w}%" for w in words]).fetchall()
    db.close()
    return {"status": "success", "match_count": len(rows),
            "matches": [{"ticket": r[0], "product": r[1], "text": r[2]} for r in rows[:8]],
            "note": "text similarity only — matches may span unrelated products and batches"}


def check_known_issue(order_number: str) -> dict:
    """Checks whether an order's product batch has a known issue, by walking the
    company graph: order -> product -> batch -> tickets -> defects.

    Args:
        order_number: The customer's order number (e.g. 8841).

    Returns:
        dict with the traversal path, any known defect, and the fix.
    """
    db = store.conn()
    row = db.execute(
        "SELECT c.name, o.id, p.name, b.id, d.title, d.fix, "
        " (SELECT COUNT(*) FROM tickets t JOIN orders oo ON t.order_id=oo.id "
        "  WHERE oo.batch_id = b.id) "
        "FROM orders o JOIN customers c ON o.customer_id=c.id "
        "JOIN products p ON p.id=o.product_id "
        "LEFT JOIN batches b ON b.id=o.batch_id "
        "LEFT JOIN defects d ON d.batch_id=b.id "
        "WHERE o.id=?", (order_number,)).fetchone()
    db.close()
    if row is None:
        return {"status": "not_found", "order_number": order_number}
    name, order_id, product, batch, title, fix, n = row
    path = (f"{name} -> order #{order_id} -> {product} -> batch {batch} "
            f"-> {n} tickets -> {title or 'no known defect'}")
    return {"status": "success", "path": path,
            "known_issue": title, "fix": fix, "connected_tickets": n}
