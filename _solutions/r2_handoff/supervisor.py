"""The supervisor console — a SEPARATE process that reads the same lumen.db.

Finds the newest session with a pending escalate_refund, shows the full chat
history a human would review, asks for a decision, and sends the answer back
into the session. adk web shows the continuation when you reload the session.

Usage (from repo root): uv run python r2_handoff/supervisor.py [--deny]
"""
import asyncio, importlib, sqlite3, sys

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

sys.path.insert(0, ".")

load_dotenv()


async def main():
    svc = SqliteSessionService(db_path="lumen.db")
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

        # We rebuild the agent from the app name, so we can only answer
        # sessions that came from an adk web agent folder. Other clients share
        # this same lumen.db on purpose — desk_app is one — and they have no
        # <app>/agent.py to import. Skip them instead of dying on the import,
        # and check BEFORE prompting so nobody reviews a call we can't answer.
        try:
            agent_mod = importlib.import_module(f"{app}.agent")
        except ModuleNotFoundError:
            print(f"↷ skipping session {sid[:8]}… — '{app}' is not an adk web "
                  f"agent folder (no {app}/agent.py to rebuild)")
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

        runner = Runner(agent=agent_mod.root_agent, app_name=app, session_service=svc)
        resp = types.Content(role="user", parts=[types.Part(
            function_response=types.FunctionResponse(
                id=pending["call_id"], name=pending["name"],
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
