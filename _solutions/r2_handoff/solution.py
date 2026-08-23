"""Rung 2 — "Please describe your issue from the beginning." The handoff."""
from google.adk.tools import LongRunningFunctionTool

from _shared.iris_agent import make_iris
from _shared.iris_tools import escalate_refund, update_ticket

root_agent = make_iris([update_ticket, LongRunningFunctionTool(escalate_refund)])
