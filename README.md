# Don't Make Me Repeat Myself

**Build a support agent with real memory — write the key lines yourself, watch every
one of them fire.**

Every support experience people hate is a memory failure:

1. "What was your order number again?" — no short-term memory
2. "Please describe your issue from the beginning." — history trapped in a process
3. "Welcome! How can I help you today?" — no long-term memory
4. "Could you describe the damage?" — after you already sent a photo
5. "We've never seen this issue." — with 37 identical tickets in the system

One customer (Maya), one flickering lamp, one week. Each rung starts BROKEN — you
run the broken behavior, open the file, write the missing line, and watch the cure land in the
adk web UI: tool chips, State tab, traces.

## Quickstart (Cloud Shell)

```bash
git clone https://github.com/cuppibla/support-memory-lab.git
cd support-memory-lab
./setup_cloudshell.sh      # API + .venv + .env (Vertex, no key) + one real model call
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

Web Preview → Change port → **8000**.

Then follow the codelab. `CODELAB.md` is the source; `dont-make-me-repeat-myself/`
is the rendered version — serve it with `claat serve` (or any static server) and
open it through Web Preview.

## How the lab works

Every rung repeats one loop:

**see the code** (`cloudshell edit <file>`) → **write the load-bearing line**
(`# TODO: `) → **run** → **watch it in the UI** (chips are clickable — read the
JSON) → **prove it on disk** (`peek.py`).

Answers live in `_solutions/` if you get stuck.

## The ladder

| Rung | The failure | The line YOU write |
|------|---------|--------------------|
| r1_short_term | re-asks within the chat | `tool_context.state[key] = value` |
| r2_handoff | handoff loses the conversation | `LongRunningFunctionTool(...)` + the `FunctionResponse` |
| r3_last_month | every new chat starts from zero | `add_session_to_memory` / `search_memory` + connect Memory Bank |
| r4_the_photo | images vanish from the record | `save_artifact(...)` in a callback |
| r5_known_issue | "never seen it" despite the data | register the graph traversal tool |
| r6_warehouse | the graph was a toy SQLite file | register the BigQuery tool, over embeddings you generate |
| desk_app | — | run the product on the same memory (`uvicorn` + `npm run dev`) |

Verified on `google-adk==2.7.1`. `_shared/` = the Lumen world + agent factory;
each rung's `tools.py` is where you work.

## Repo map

| | |
|---|---|
| `CODELAB.md` | the codelab source — `dont-make-me-repeat-myself/` is the rendered copy (`claat export`) |
| `r1_…` – `r6_…` | the starters you edit, one agent package per rung |
| `_solutions/` | complete versions, named `solution.py` so `adk web` won't list them as agents |
| `_shared/` | the Lumen world (40 tickets, 6 tables), the 7 tools, the agent factory |
| `desk_app/` | the React + FastAPI support desk, on the same services |
| `warehouse/` | the CSVs you load into BigQuery |
| `codelab-assets/` | every image in the codelab, with hand-authored SVG sources in `src/` |
