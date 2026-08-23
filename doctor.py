"""Pre-flight check. Run me before the workshop starts."""
import os, sys

ok = True
v = sys.version_info
print(f"{'✅' if v >= (3, 10) else '❌'} python {v.major}.{v.minor}")
ok &= v >= (3, 10)
try:
    import google.adk
    print(f"✅ google-adk {google.adk.__version__}")
except ImportError as e:
    print(f"❌ google-adk missing: {e}"); ok = False
from dotenv import load_dotenv
load_dotenv()
try:
    from google import genai
    if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true":
        client = genai.Client()  # Vertex: project + ADC from the environment
        label = f"Vertex AI · {os.environ.get('GOOGLE_CLOUD_PROJECT')} — no API key anywhere"
    else:
        key = os.environ.get("GOOGLE_API_KEY", "")
        assert len(key) >= 20, "GOOGLE_API_KEY missing — or set GOOGLE_GENAI_USE_VERTEXAI=True"
        client = genai.Client(api_key=key)
        label = "AI Studio API key"
    client.models.generate_content(model="gemini-3-flash-preview", contents="say ok")
    print(f"✅ model answers ({label})")
except Exception as e:
    print(f"❌ model call failed: {str(e)[:140]}"); ok = False
print("🎉 ready — launch adk web (see the codelab)" if ok else "fix the ❌ above, then re-run")
sys.exit(0 if ok else 1)
