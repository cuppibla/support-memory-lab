"""Rung 3 — "Welcome! How can I help you today?" Last month exists now."""
from google.adk.tools import LongRunningFunctionTool

from _shared.iris_agent import make_iris
from r2_handoff.tools import escalate_refund

from .tools import close_ticket, recall_history, update_ticket

root_agent = make_iris([update_ticket, LongRunningFunctionTool(escalate_refund),
                        close_ticket, recall_history])
