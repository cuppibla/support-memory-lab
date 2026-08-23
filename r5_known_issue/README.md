# Rung 5 — "We've never seen this issue."

> This folder is a STARTER — it has a `# TODO(you):` hole the codelab walks you
> through. Answers: `_solutions/r5_known_issue/solution.py`.


**The failure:** support says "never seen it" while 37 tickets on the same batch sit in
the system.
**The fix:** institutional memory — the company graph that exists in plain tables:
customers → orders → products → batches → tickets → defects.

## What's wired

Two retrieval tools, on purpose:
- `search_tickets(text)` — naive text similarity over ALL tickets. Fast, plausible, blind.
- `check_known_issue(order_number)` — a FIXED, parameterized traversal. The agent never
  writes the query; it calls a governed tool and quotes the path it returns.

The world lives in `_shared/lumen_world.db` (built by `_shared/store.py`).

## Try it (adk web → agent `r5_known_issue`)

1. `Search the ticket archive for other flickering lamps like mine.`
   → ~40 matches, spanning LumenGlow v1, v2 AND Halo Mini. Similar words — but which
   of these have anything to do with THIS customer? The tool cannot say.
2. `Is my problem a known issue? My order number is 8841.`
   → the traversal answers with a citation path:
   `Maya -> order #8841 -> LumenGlow v2 -> batch B7 -> 37 tickets -> Flicker + base crack (driver defect)` · fix: firmware 2.1

**The two beats:** similar is not connected · the agent never writes the query.

## Production

This graph already exists in your warehouse. In BigQuery it's one zero-copy statement
(`CREATE PROPERTY GRAPH`) over existing tables, then the same three-stage loop:
vector search finds WHERE to look, graph traversal finds WHAT's connected, the model
answers with a citation trail. (Live demo in the workshop.)
