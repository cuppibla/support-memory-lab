# Rung 2 — "Please describe your issue from the beginning."

> This folder is a STARTER — it has a `# TODO: ` hole the codelab walks you
> through. Answers: `_solutions/r2_handoff/solution.py`.


**The failure:** the human who takes over can't see the chat, so the customer starts over.
**The fix:** persistent sessions (`sqlite://lumen.db`) + `LongRunningFunctionTool` —
the run PARKS while a different process reads the same history and answers.

## What's wired

`escalate_refund(amount, reason)` wrapped in `LongRunningFunctionTool`: it returns
`{"status": "pending"}` and the run stops. `supervisor.py` (this folder) is the second
process: it finds the pending call in lumen.db, prints the full history, and sends the
`function_response` that resumes the conversation.

## Try it (adk web → agent `r2_handoff`)

1. `This replacement lamp is broken too. I want an $80 refund for order 8841.`
   → Iris parks: "a supervisor is reviewing."
2. In a SECOND terminal, from repo root:

```bash
uv run python r2_handoff/supervisor.py
```

   Read the history it prints — that's the point — then press Enter to approve.
3. Back in adk web, reload the session (session picker → your session).

**What must be true:** the reloaded session shows the approval event and Iris's
continuation ("refund approved… 3-5 days") — and Maya never repeated a word.

## The beat

A human can only "check the chat history" if the history lives outside the process.
Persistence is what makes human-in-the-loop possible — not a separate feature.
