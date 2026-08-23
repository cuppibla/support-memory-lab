"""Rung 5 — "We've never seen this issue." Institutional memory: the graph."""
from google.adk.tools import LongRunningFunctionTool

from _shared.iris_agent import make_iris
from r2_handoff.tools import escalate_refund
from r3_last_month.tools import close_ticket, recall_history, update_ticket
from r4_the_photo.tools import record_damage

from .tools import check_known_issue, search_tickets  # noqa: F401

# Iris only has the blind text search right now — run the trap first, then
# give her the graph. (Its instruction rule wires itself in automatically.)
root_agent = make_iris([update_ticket, LongRunningFunctionTool(escalate_refund),
                        close_ticket, recall_history, record_damage,
                        search_tickets,
                        # TODO: check_known_issue,
                        ])
