"""Rung 4 tools — the model does the seeing; this tool records what was seen."""

from google.adk.tools import ToolContext


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
