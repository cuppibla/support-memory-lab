"""Rung 4 — "Could you describe the damage?" The photo becomes memory."""
from google.adk.tools import LongRunningFunctionTool

from _shared.iris_agent import make_iris
from r2_handoff.tools import escalate_refund
from r3_last_month.tools import close_ticket, recall_history, update_ticket

from .callbacks import stash_uploaded_photo
from .tools import record_damage

root_agent = make_iris(
    [update_ticket, LongRunningFunctionTool(escalate_refund),
     close_ticket, recall_history, record_damage],
    before_agent_callback=stash_uploaded_photo,
)
