# Rung 6 — the warehouse

> This folder is a STARTER — delete the `# TODO: ` prefix in `agent.py`.
> Answers: `_solutions/r6_warehouse/solution.py`.

**The failure:** rung 5's graph lived in a lab SQLite file. Real institutional
memory lives in the company warehouse.
**What you build:** GCS → BigQuery (structured tables) → embeddings generated
in-place → two governed tools: `warehouse_search` (semantic, meaning not
keywords) and `warehouse_known_issue` (the traversal, at scale).

The full command sequence (bucket, `bq load`, connection, `CREATE MODEL`,
`ML.GENERATE_EMBEDDING`, `VECTOR_SEARCH`) is in the codelab — every command is
real and verified. The agent never writes SQL: both tools are fixed,
parameterized queries in `tools.py`.
