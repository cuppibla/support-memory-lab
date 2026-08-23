"""Rung 1 — "What was your order number again?" Iris earns a ticket (state)."""
from _shared.iris_agent import make_iris

from .tools import update_ticket

root_agent = make_iris([update_ticket])
