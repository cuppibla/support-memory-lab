"""Rung 6 — the warehouse. Same Iris, but her institutional memory now lives in
BigQuery: structured tables you loaded from GCS, embeddings generated in-place."""
from google.adk.tools import LongRunningFunctionTool

from _shared.iris_agent import make_iris
from r2_handoff.tools import escalate_refund
from r3_last_month.tools import close_ticket, recall_history, update_ticket
from r4_the_photo.tools import record_damage

from .tools import warehouse_known_issue, warehouse_search  # noqa: F401

root_agent = make_iris([update_ticket, LongRunningFunctionTool(escalate_refund),
                        close_ticket, recall_history, record_damage,
                        warehouse_known_issue,
                        # TODO: warehouse_search,
                        ])
