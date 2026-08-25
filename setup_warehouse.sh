#!/bin/bash
# The warehouse, provisioned. Everything this script does is plumbing the
# codelab used to make you type by hand: a bucket, six CSV loads, a BigQuery
# connection, one IAM grant, and the remote embedding model.
#
# It prints each step as it goes, and it is safe to re-run — every step either
# replaces what it made or skips what already exists.
#
# What it deliberately does NOT do: embed the tickets, or search them. Those
# two statements are the lesson, and you run them yourself in the console.
set -e
cd "$(dirname "$0")"

# Pinned to match the lab environment's allowed_locations. Everything —
# bucket, dataset, connection, model — has to agree on this one region, and
# a mismatch here is the classic "was not found in location" error later.
REGION="us-west1"

PROJECT=$(gcloud config get-value project 2>/dev/null)
[ -z "$PROJECT" ] && { echo "Set a project first: gcloud config set project <ID>"; exit 1; }
BUCKET="gs://${PROJECT}-lumen"
echo "==> Project: $PROJECT"
echo "==> Region:  $REGION"

echo "==> Enabling BigQuery, BigQuery Connection and Cloud Storage APIs…"
gcloud services enable \
  bigquery.googleapis.com \
  bigqueryconnection.googleapis.com \
  storage.googleapis.com

echo "==> Bucket: $BUCKET"
if gcloud storage buckets describe "$BUCKET" >/dev/null 2>&1; then
  echo "    already exists — reusing"
else
  gcloud storage buckets create "$BUCKET" --location="$REGION"
fi

echo "==> Uploading the six CSVs…"
gcloud storage cp warehouse/*.csv "$BUCKET/"

echo "==> Dataset: lumen"
if bq --project_id="$PROJECT" show --dataset "${PROJECT}:lumen" >/dev/null 2>&1; then
  echo "    already exists — reusing"
else
  bq --project_id="$PROJECT" mk --location="$REGION" --dataset lumen
fi

# --replace makes each load idempotent: re-running rebuilds the table rather
# than appending a second copy of every row.
echo "==> Loading six tables (schemas are the company's, not ours)…"
load() {
  echo "    - lumen.$1"
  bq --project_id="$PROJECT" load --replace --source_format=CSV --skip_leading_rows=1 \
    "lumen.$1" "$BUCKET/$1.csv" "$2" >/dev/null
}
load customers "id:STRING,name:STRING"
load products  "id:STRING,name:STRING"
load batches   "id:STRING,product_id:STRING"
load orders    "id:STRING,customer_id:STRING,product_id:STRING,batch_id:STRING"
load tickets   "id:STRING,order_id:STRING,text:STRING"
load defects   "batch_id:STRING,title:STRING,fix:STRING"

echo "==> Connection: ${REGION}.vertex_conn"
if bq --project_id="$PROJECT" show --connection "${PROJECT}.${REGION}.vertex_conn" >/dev/null 2>&1; then
  echo "    already exists — reusing"
else
  bq --project_id="$PROJECT" mk --connection \
    --location="$REGION" --connection_type=CLOUD_RESOURCE vertex_conn
fi

# The connection owns a service account that is created WITH it and starts
# with no permissions at all. BigQuery uses that account to call Vertex on
# your behalf, so it needs roles/aiplatform.user — displayed in the console as
# "Agent Platform User" since Vertex AI moved under the Agent Platform brand.
CONN_SA=$(bq --project_id="$PROJECT" show --format=json --connection "${PROJECT}.${REGION}.vertex_conn" \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['cloudResource']['serviceAccountId'])")
echo "==> Granting roles/aiplatform.user to $CONN_SA"
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:$CONN_SA" \
  --role=roles/aiplatform.user \
  --condition=None >/dev/null
echo "    granted"

# CREATE MODEL is the first thing that actually exercises the grant, and IAM
# is eventually consistent — so this is where "does not have the permission to
# access or use the endpoint" shows up for a minute or so after a grant that
# genuinely worked. Retry rather than hand that error to the learner.
echo "==> Creating the remote embedding model (waits for IAM to propagate)…"
MODEL_SQL='CREATE OR REPLACE MODEL lumen.embedder
  REMOTE WITH CONNECTION `'"${REGION}"'.vertex_conn`
  OPTIONS (ENDPOINT = "gemini-embedding-001")'

# Capture BOTH streams. bq puts its progress line ("Waiting on bqjob_… DONE")
# on stderr but the actual failure ("Error in query string: … does not have the
# permission …") on stdout, so discarding stdout would throw away the only text
# worth matching on — and would print the progress line as if it were the error.
LOG=/tmp/setup_warehouse_embedder.log
for attempt in $(seq 1 10); do
  if bq --project_id="$PROJECT" query --use_legacy_sql=false "$MODEL_SQL" >"$LOG" 2>&1; then
    echo "    created on attempt $attempt"
    break
  fi
  if grep -qi "permission\|denied\|does not have" "$LOG" && [ "$attempt" -lt 10 ]; then
    echo "    attempt $attempt: IAM still propagating, retrying in 20s…"
    sleep 20
    continue
  fi
  echo "!!! CREATE MODEL failed:"
  cat "$LOG"
  exit 1
done

echo
echo "==> Verifying"
TICKETS=$(bq --project_id="$PROJECT" query --use_legacy_sql=false --format=csv \
  "SELECT COUNT(*) FROM lumen.tickets" | tail -1)
echo "    tables loaded, lumen.tickets rows: $TICKETS"
echo "    models:"
bq --project_id="$PROJECT" ls --models lumen | tail -n +3 | sed 's/^/      /'

echo
echo "✅ Warehouse ready. The graph is in BigQuery and Vertex is reachable from SQL."
echo "   Next, in the BigQuery console: embed the tickets, then search them."
