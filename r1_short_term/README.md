# Rung 1 — "What was your order number again?"

> This folder is a STARTER — it has a `# TODO(you):` hole the codelab walks you
> through. Answers: `_solutions/r1_short_term/solution.py`.


**The failure:** the agent re-asks things the customer said five messages ago.
**The fix:** `session.state` — a typed ticket your code can trust, living next to the transcript.

## What's wired

One tool: `update_ticket(field, value)` writes `ticket_*` keys into `tool_context.state`.
The instruction tells Iris to record every concrete detail before replying, and to never re-ask.

## Try it (adk web → agent `r1_short_term`)

1. `Hi, my lamp keeps flickering. Order number is 8841, it's a LumenGlow v2.`
2. `Quick check - what order number do you have for me, and which lamp is it?`

**What must be true:** three `update_ticket` chips in the event feed; the State tab shows
`ticket_order_number / ticket_product / ticket_symptom`; turn 2 answers without re-asking.

## Prove it on disk

```bash
uv run python peek.py
```

The session holds TWO things: the transcript (what the model reads) and the ticket
(typed state your code branches on). That distinction carries the whole lab.

## The cliff this rung ends on

Stop the server (Ctrl-C) and relaunch adk web with ONE flag changed:
`--session_service_uri "memory://"` — your session list is empty. Nothing survived
the process. Relaunch with `sqlite:///lumen.db` and everything is back.
The difference is one URI on a command you typed. That's rung 2's story.
