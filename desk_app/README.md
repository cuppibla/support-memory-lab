# The desk goes to production — Lumen Support Desk

Everything you built in rungs 1–5, behind a real product face. The teaching claim:
**the UI is a client of the memory architecture, not the owner of it.** Same Iris
(rung 5's), same `lumen.db`, same artifact store. Nothing about memory changed.

## Run it (two terminals — adk web can stay up; the backend uses port 8080)

```bash
source .venv/bin/activate
uvicorn main:app --app-dir desk_app/backend --port 8080
```

```bash
cd desk_app/frontend
npm install
npm run dev
```

Web Preview → Change port → **5173**.

## Replay the story

1. Ask for an $80 refund → the dot goes amber, the Supervisor card lights up.
2. Read the history (right panel), click **Approve** → the conversation continues.
   That button sends the exact `function_response` you sent by hand in rung 2.
3. 📎 upload the lamp photo, ask "is my problem a known issue?" → Iris reads B7 off
   the image and quotes the citation path.

## Code walk (~15 min)

- `backend/main.py` (~150 lines): one Runner wired to `SqliteSessionService(lumen.db)`
  + `FileArtifactService`. `/api/chat` builds the same multimodal Content adk web
  builds; `/api/approve` is `supervisor.py` as an endpoint.
- `frontend/src/App.jsx` (~180 lines): two panels polling `/api/session`. The upload
  button downscales client-side to ≤512px before anything touches the wire.
