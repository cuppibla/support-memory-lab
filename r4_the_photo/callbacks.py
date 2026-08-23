"""Rung 4 callback — every uploaded photo deserves a permanent home."""

from google.adk.agents.callback_context import CallbackContext


async def stash_uploaded_photo(callback_context: CallbackContext) -> None:
    """Runs before each turn: if the user attached an image, save it as an artifact."""
    content = callback_context.user_content
    if not content or not content.parts:
        return
    for part in content.parts:
        blob = getattr(part, "inline_data", None)
        if blob and (blob.mime_type or "").startswith("image/"):
            # ── KEEP THE FILE ─ delete the "# TODO: " prefix ──────────────
            # TODO: await callback_context.save_artifact("user:lamp_photo.jpg", part)
            pass
