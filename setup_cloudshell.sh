#!/bin/bash
# Cloud Shell setup. Everything this script does is listed in the codelab —
# and it prints each step as it goes.
set -e
cd "$(dirname "$0")"

PROJECT=$(gcloud config get-value project 2>/dev/null)
[ -z "$PROJECT" ] && { echo "Set a project first: gcloud config set project <ID>"; exit 1; }
echo "==> Project: $PROJECT"

echo "==> Enabling the Vertex AI API (aiplatform.googleapis.com)…"
gcloud services enable aiplatform.googleapis.com

echo "==> Creating .venv and installing pinned deps (requirements.txt)…"
python3 -m venv .venv
source .venv/bin/activate
pip install --quiet -r requirements.txt

echo "==> Writing .env (Vertex mode — no API key anywhere)…"
cat > .env << ENVEOF
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_PROJECT=$PROJECT
GOOGLE_CLOUD_LOCATION=global
ENVEOF

echo "==> Pre-flight (one real model call — a broken project fails HERE, not mid-lab):"
python doctor.py
