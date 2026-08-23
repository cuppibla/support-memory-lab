# Rung 3 — "Welcome! How can I help you today?"

> This folder is a STARTER — it has a `# TODO(you):` hole the codelab walks you
> through. Answers: `_solutions/r3_last_month/solution.py`.


**The failure:** a returning customer with last month's ticket gets treated as a stranger.
**The fix:** a memory service. Sessions are silos — `close_ticket` FILES a conversation
(`add_session_to_memory`), `recall_history` SEARCHES the archive from any new session.

## Try it (adk web → agent `r3_last_month`)

Session A:
1. `My LumenGlow v2 was flickering, order 8841. The firmware update you suggested fixed it! Please close my ticket.`
   → watch the `close_ticket` chip: the write policy, visible as a tool call.

Session B (NEW SESSION button):
2. First try the vague question: `Have I contacted you before?`
   → Iris likely comes up EMPTY. Not a bug — a lesson (see below).
3. Now: `Did I report a flickering LumenGlow lamp to you before?`

**What must be true:** the recall_history chip fires and Iris answers with the old
ticket's facts (flickering, LumenGlow v2, #8841).

## Why the vague question failed

The local `InMemoryMemoryService` matches KEYWORDS, not meaning. "Have I contacted
you before" shares no content words with last month's transcript. Production memory
(Vertex AI Memory Bank, embeddings) matches meaning — but "similar words ≠ the right
memory" stays true at every scale. Rung 5 turns that into the main event.

## The trap, named

Your old session was already sitting in lumen.db during step 2 of this rung — and it
didn't help at all. **Filed is not remembered.** Storage you can't recall at the right
moment is not memory.

Note: this memory service lives inside the adk web process. Restart the server and the
archive is gone (sessions survive; the memory index doesn't). That fragility is exactly
why managed memory services exist — see the wrap.
