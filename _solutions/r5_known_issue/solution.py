"""Rung 5 — "We've never seen this issue." Institutional memory: the graph."""
from google.adk.tools import LongRunningFunctionTool

from _shared.iris_agent import make_iris
from _shared.iris_tools import (check_known_issue, close_ticket, escalate_refund,
                                recall_history, record_damage, search_tickets,
                                update_ticket)

root_agent = make_iris([update_ticket, LongRunningFunctionTool(escalate_refund),
                        close_ticket, recall_history, record_damage,
                        search_tickets, check_known_issue])
