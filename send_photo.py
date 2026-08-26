"""Send Maya's photo to Iris without a browser file picker.

Rung 4 normally has you click 📎 in the dev UI and attach a photo from your
machine. Some managed browsers block file uploads outright (Incognito under
corporate policy is the common one), which makes that step impossible through
the UI.

Nothing about the lesson requires the UI. An uploaded image is just an inline
image Part on the user's message, and `stash_uploaded_photo` fires on any turn
that carries one. This script builds that same message from the copy of the
photo already in the repo and runs one turn against the SAME services adk web
uses, so the result lands in lumen.db and shows up in the dev UI like any other
conversation.

Usage (from repo root):  python send_photo.py [path/to/photo.jpg]
"""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.artifacts.file_artifact_service import FileArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))  # so `r4_the_photo` imports from any cwd
load_dotenv(REPO / ".env")

PHOTO = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "_shared/maya/lamp_photo.jpg"
PROMPT = "Here is a photo of my broken lamp. What do you see? Please record the damage."

# adk web names the app after the agent folder and uses "user" as the user id.
# Matching both is what makes this session appear in the dev UI's session list.
APP, USER = "r4_the_photo", "user"
SID = "photo-no-upload"


async def main():
    if not PHOTO.exists():
        print(f"No photo at {PHOTO}")
        print("Pass one explicitly:  python send_photo.py path/to/photo.jpg")
        return

    from r4_the_photo.agent import root_agent

    # The same three services adk web builds from its flags — same SQLite file,
    # same artifacts directory. That is why the run is visible in the dev UI.
    session_service = SqliteSessionService(db_path=str(REPO / "lumen.db"))
    artifact_service = FileArtifactService(root_dir=REPO / "artifacts_store")
    runner = Runner(agent=root_agent, app_name=APP,
                    session_service=session_service,
                    memory_service=InMemoryMemoryService(),
                    artifact_service=artifact_service)

    if await session_service.get_session(app_name=APP, user_id=USER, session_id=SID) is None:
        await session_service.create_session(app_name=APP, user_id=USER, session_id=SID)

    # This is exactly what the 📎 button produces: a text part and an inline
    # image part on one user message.
    message = types.Content(role="user", parts=[
        types.Part.from_text(text=PROMPT),
        types.Part(inline_data=types.Blob(
            mime_type="image/jpeg", data=PHOTO.read_bytes())),
    ])

    print(f"📎 {PHOTO.name} ({PHOTO.stat().st_size:,} bytes) -> {APP}/{SID}")
    print("─" * 60)
    async for ev in runner.run_async(user_id=USER, session_id=SID, new_message=message):
        for part in (ev.content.parts if ev.content else []) or []:
            fc = getattr(part, "function_call", None)
            fr = getattr(part, "function_response", None)
            if fc:
                print(f"  ⚡ {fc.name} {dict(fc.args or {})}")
            elif fr:
                print(f"  ✓ {fr.name} -> {fr.response}")
        if ev.is_final_response() and ev.content and ev.content.parts \
                and ev.content.parts[0].text:
            print("─" * 60)
            print(f"IRIS: {ev.content.parts[0].text.strip()}")

    print()
    print("✅ done — open the dev UI, pick r4_the_photo, and load the session")
    print(f"   named '{SID}' from the session list to see this conversation.")


asyncio.run(main())
