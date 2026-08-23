"""Create the Agent Engine instance that hosts your Memory Bank.

Ten lines, no magic. It calls the Vertex AI SDK once and prints the id you'll
use everywhere else. Run it yourself:

    python r3_last_month/create_memory_bank.py
"""

import os

import vertexai
from vertexai import agent_engines

project = os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("MEMORY_BANK_LOCATION", "us-central1")  # regional — NOT the model endpoint
print(f"Creating an Agent Engine instance in {project} / {location} …")

vertexai.init(project=project, location=location)
engine = agent_engines.create(display_name="support-memory-lab")

engine_id = engine.resource_name.split("/")[-1]
print(f"\nDone. resource: {engine.resource_name}")
print(f"Your AGENT_ENGINE_ID = {engine_id}")
print(f"\nNext: relaunch adk web with your archive in the cloud —")
print(f"add this flag to the adk web command you already know:")
print(f'  --memory_service_uri "agentengine://{engine.resource_name}"')
