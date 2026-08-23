"""Rung 3 — "Welcome! How can I help you today?" Last month exists now."""
from google.adk.tools import LongRunningFunctionTool

from _shared.iris_agent import make_iris
from _shared.iris_tools import (close_ticket, escalate_refund, recall_history,
                                update_ticket)

root_agent = make_iris([update_ticket, LongRunningFunctionTool(escalate_refund),
                        close_ticket, recall_history])
