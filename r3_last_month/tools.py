"""Rung 3 tools — the write policy and the recall policy, each one TODO away."""

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
    filed = False
    # ── THE WRITE POLICY ─ delete the "# TODO: " prefix ───────────────────
    # TODO: await memory_service.add_session_to_memory(session); filed = True
    return {"status": "success", "filed_to_memory": filed, "resolution": resolution}


async def recall_history(query: str, tool_context: ToolContext) -> dict:
    """Searches this customer's past support conversations.

    Args:
        query: What to look for in past conversations.

    Returns:
        dict with any past facts found.
    """
    result = None
    # ── THE RECALL POLICY ─ delete the "# TODO: " prefix ──────────────────
    # TODO: result = await tool_context.search_memory(query)
    if result is None:
        return {"status": "empty", "past_conversations": [],
                "note": "recall not wired yet (TODO)"}
    memories = []
    for m in getattr(result, "memories", []) or []:
        content = getattr(m, "content", None)
        if content and content.parts:
            memories.extend(p.text for p in content.parts if getattr(p, "text", None))
    return {"status": "success", "past_conversations": memories[:10]}
