"""The supervisor console — a SEPARATE process that reads the same lumen.db.

Finds the newest session with a pending escalate_refund, shows the full chat
history a human would review, asks for a decision, and sends the answer back
into the session. adk web shows the continuation when you reload the session.

Usage (from repo root): uv run python r2_handoff/supervisor.py [--deny]
"""
import asyncio, sqlite3, sys

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

sys.path.insert(0, ".")

load_dotenv()


async def main():
    svc = None
    # ── THE WHOLE TRICK ─ delete the "# TODO: " prefix ────────────────────
    # This is the SAME file, opened with the SAME service class, that adk web
    # is using right now. That one line is why a second process can take over.
    # TODO: svc = SqliteSessionService(db_path="lumen.db")
    if svc is None:
        print("Connect to the session store first — open this file:")
        print("  cloudshell edit r2_handoff/supervisor.py   (see codelab Rung 2)")
        return
    rows = sqlite3.connect("lumen.db").execute(
        "SELECT app_name, user_id, id FROM sessions ORDER BY update_time DESC").fetchall()
    for app, user_id, sid in rows:
        s = await svc.get_session(app_name=app, user_id=user_id, session_id=sid)
        answered = set()
        pending = None
        for ev in s.events:
            for part in (ev.content.parts if ev.content else []) or []:
                fr = getattr(part, "function_response", None)
                if (fr and fr.name == "escalate_refund"
                        and (fr.response or {}).get("status") != "pending"):
                    answered.add(fr.id)
        for ev in s.events:
            if ev.long_running_tool_ids:
                for part in ev.content.parts or []:
                    fc = getattr(part, "function_call", None)
                    if fc and fc.id in ev.long_running_tool_ids and fc.id not in answered:
                        pending = {"call_id": fc.id, "name": fc.name, "args": fc.args}
        if not pending:
            continue

        print(f"⏸ PENDING: {pending['name']} {pending['args']}  (session {sid[:8]}…)")
        print("─" * 60)
        for ev in s.events:
            for part in (ev.content.parts if ev.content else []) or []:
                if getattr(part, "text", None):
                    print(f"  [{ev.author}] {part.text[:100]}")
        print("─" * 60)
        deny = "--deny" in sys.argv
        decision = ("denied", "Refund denied. Offer a replacement instead.") if deny \
            else ("approved", "Refund approved. Tell the customer it arrives in 3-5 days.")
        input(f"Press Enter to send: {decision[0].upper()} > ")

        import importlib
        agent_mod = importlib.import_module(f"{app}.agent")
        runner = Runner(agent=agent_mod.root_agent, app_name=app, session_service=svc)
        # The answer to the parked call — read it like a sentence: the id names
        # WHICH parked call, the name must match the tool, the response is what
        # the tool finally "returns".
        resp = types.Content(role="user", parts=[types.Part(
            function_response=types.FunctionResponse(
                id=pending["call_id"],   # which parked call we're answering
                name=pending["name"],    # must match the tool name
                response={"status": decision[0], "approved_by": "supervisor",
                          "note": decision[1]}))])
        async for ev in runner.run_async(user_id=user_id, session_id=sid, new_message=resp):
            if ev.is_final_response() and ev.content and ev.content.parts \
                    and ev.content.parts[0].text:
                print(f"\nIRIS (resumed): {ev.content.parts[0].text[:200]}")
        print("\n✅ done — reload the session in adk web to see the continuation")
        return
    print("no pending escalation found — ask Iris for a refund over $50 first")


asyncio.run(main())
