"""Rung 2 — "Please describe your issue from the beginning." The handoff."""
# TODO: from google.adk.tools import LongRunningFunctionTool

from _shared.iris_agent import make_iris

from .tools import escalate_refund, update_ticket

# Right now escalate_refund is an ORDINARY tool — the turn runs straight
# through it and no human ever gets a say. Park the run instead:
escalation = escalate_refund
# TODO: escalation = LongRunningFunctionTool(escalate_refund)
root_agent = make_iris([update_ticket, escalation])
