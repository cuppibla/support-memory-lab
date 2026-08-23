"""Lumen Support Desk — the agent backend.

The teaching point of this file: it changes NOTHING about memory. Same Iris
(rung 5's), same lumen.db sessions, same artifact store as adk web. The app
is just another client of the memory architecture, not the owner of it.

Run from repo root:  uvicorn main:app --app-dir desk_app/backend --port 8080
"""

import base64
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv

load_dotenv(REPO / ".env")

from fastapi import FastAPI
from google.adk.artifacts.file_artifact_service import FileArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types
from pydantic import BaseModel

from _solutions.r5_known_issue.solution import root_agent

APP, USER, SID = "desk_app", "maya", "desk-maya"

# ---- the plumbing adk web hides behind flags ------------------------------
# SessionService: WHERE conversations live. This is the same class and the
# same file that `--session_service_uri "sqlite:///lumen.db"` constructs.
session_service = SqliteSessionService(db_path=str(REPO / "lumen.db"))

# MemoryService: the archive. Default = in-process keyword memory (rung 3's
# starting point). Set AGENT_ENGINE to your rung-3c resource name
# (projects/.../reasoningEngines/ID) and the SAME two policies you wrote —
# add_session_to_memory and search_memory — talk to Memory Bank instead.
AGENT_ENGINE = os.environ.get("AGENT_ENGINE", "")
if AGENT_ENGINE:
    from google.adk.memory import VertexAiMemoryBankService

    memory_service = VertexAiMemoryBankService(
        project=os.environ["GOOGLE_CLOUD_PROJECT"],
        location=os.environ.get("MEMORY_BANK_LOCATION", "us-central1"),
        agent_engine_id=AGENT_ENGINE.split("/")[-1],
    )
else:
    memory_service = InMemoryMemoryService()

# ArtifactService: where files live — same directory as adk web's file:// flag.
artifact_service = FileArtifactService(root_dir=REPO / "artifacts_store")

# The Runner: ADK's engine. One call — run_async(user_id, session_id,
# new_message) — runs the agent one turn against exactly these services.
# adk web builds one of these per agent folder; here you can read yours.
runner = Runner(agent=root_agent, app_name=APP, session_service=session_service,
                memory_service=memory_service, artifact_service=artifact_service)

app = FastAPI()


class ChatIn(BaseModel):
    text: str
    image_b64: str | None = None


class ApproveIn(BaseModel):
    decision: str  # "approved" | "denied"


async def _get_or_create():
    s = await session_service.get_session(app_name=APP, user_id=USER, session_id=SID)
    if s is None:
        s = await session_service.create_session(app_name=APP, user_id=USER, session_id=SID)
    return s


def _find_pending(session):
    answered = set()
    for ev in session.events:
        for part in (ev.content.parts if ev.content else []) or []:
            fr = getattr(part, "function_response", None)
            if fr and fr.name == "escalate_refund" and (fr.response or {}).get("status") != "pending":
                answered.add(fr.id)
    pending = None
    for ev in session.events:
        if ev.long_running_tool_ids:
            for part in ev.content.parts or []:
                fc = getattr(part, "function_call", None)
                if fc and fc.id in ev.long_running_tool_ids and fc.id not in answered:
                    pending = {"call_id": fc.id, "name": fc.name, "args": fc.args}
    return pending


def _view(session):
    messages, trail = [], None
    for ev in session.events:
        who = "maya" if ev.author == "user" else "iris"
        for part in (ev.content.parts if ev.content else []) or []:
            if getattr(part, "text", None) and not getattr(part, "thought", False):
                messages.append({"who": who, "text": part.text})
            if getattr(part, "inline_data", None):
                messages.append({"who": who, "photo": True})
            fr = getattr(part, "function_response", None)
            if fr and fr.name == "check_known_issue" and (fr.response or {}).get("path"):
                trail = {"path": fr.response["path"], "fix": fr.response.get("fix")}
    ticket = {k: v for k, v in session.state.items()
              if k.startswith(("ticket_", "photo_"))}
    return {"messages": messages, "ticket": ticket,
            "pending": _find_pending(session), "trail": trail}


async def _run(new_message):
    async for _ in runner.run_async(user_id=USER, session_id=SID, new_message=new_message):
        pass
    s = await session_service.get_session(app_name=APP, user_id=USER, session_id=SID)
    return _view(s)


@app.get("/api/session")
async def get_session():
    return _view(await _get_or_create())


@app.post("/api/chat")
async def chat(body: ChatIn):
    await _get_or_create()
    parts = [types.Part.from_text(text=body.text)]
    if body.image_b64:
        parts.append(types.Part(inline_data=types.Blob(
            mime_type="image/jpeg", data=base64.b64decode(body.image_b64))))
    return await _run(types.Content(role="user", parts=parts))


@app.post("/api/approve")
async def approve(body: ApproveIn):
    s = await _get_or_create()
    pending = _find_pending(s)
    if not pending:
        return _view(s)
    note = ("Refund approved. Tell the customer it arrives in 3-5 days."
            if body.decision == "approved" else
            "Refund denied. Offer a replacement instead.")
    resp = types.Content(role="user", parts=[types.Part(
        function_response=types.FunctionResponse(
            id=pending["call_id"], name=pending["name"],
            response={"status": body.decision, "approved_by": "supervisor", "note": note}))])
    return await _run(resp)


@app.post("/api/reset")
async def reset():
    s = await session_service.get_session(app_name=APP, user_id=USER, session_id=SID)
    if s is not None:
        await session_service.delete_session(app_name=APP, user_id=USER, session_id=SID)
    return {"ok": True}


# ---- the built frontend, same port (Cloud Shell single Web Preview) ----
from fastapi.staticfiles import StaticFiles

DIST = REPO / "desk_app" / "frontend" / "dist"
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
