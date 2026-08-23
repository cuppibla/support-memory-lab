"""What is ACTUALLY on disk? Dumps sessions, events, and state from lumen.db.

Usage: uv run python peek.py [session_id]
"""
import json, sqlite3, sys

db = sqlite3.connect("lumen.db")
sessions = db.execute(
    "SELECT id, app_name, user_id, json_extract(state,'$') FROM sessions "
    "ORDER BY update_time").fetchall()
if not sessions:
    print("lumen.db: no sessions yet"); sys.exit(0)
want = sys.argv[1] if len(sys.argv) > 1 else None
for sid, app, user, state in sessions:
    if want and not sid.startswith(want):
        continue
    n = db.execute("SELECT COUNT(*) FROM events WHERE session_id=?", (sid,)).fetchone()[0]
    print(f"\n=== session {sid[:8]}…  agent={app}  user={user}  events={n}")
    print(f"    state: {state}")
    for (event_data,) in db.execute(
            "SELECT event_data FROM events WHERE session_id=? ORDER BY timestamp", (sid,)):
        if not event_data:
            continue
        e = json.loads(event_data)
        c = e.get("content") or {}
        for part in c.get("parts", []):
            if part.get("text"):
                print(f"    [{c.get('role','?')}] {part['text'][:90]}")
            if part.get("function_call"):
                print(f"    [call] {part['function_call']['name']}")
            if part.get("inline_data"):
                print(f"    [file] {part['inline_data'].get('mime_type')} "
                      f"({len(part['inline_data'].get('data',''))//1024}KB b64)")
