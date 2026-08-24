author: Qingyue (Annie) Wang
summary: Every support experience people hate is a memory failure. Fix five of them yourself — write the load-bearing line, launch adk web, type to Iris, and watch every mechanism fire. Cloud Shell, ADK, Gemini, and one very patient customer named Maya.
id: agent-memory-layer-by-layer
categories: adk,agents,memory,gemini,cloudshell
environments: Web
status: Draft
feedback link: https://github.com/cuppibla/support-memory-lab/issues

# Agent Memory, Layer by Layer: Build a Support Agent That Remembers

## Overview
Duration: 6:00

![hero](https://storage.googleapis.com/support-memory-lab-assets/img/hero.png)

You know these five sentences. Everyone knows these five sentences:

1. *"What was your order number again?"*
2. *"You've been transferred. Please describe your issue from the beginning."*
3. *"Welcome! How can I help you today? 😊"* — said to a customer with an open ticket from last month
4. *"Could you describe the damage?"* — after you already sent a photo
5. *"Hmm, we've never seen this issue."* — while 37 tickets on the same batch sit in the system

Every one of them is a **memory failure** — a specific, nameable gap in how the system remembers. And "memory" is not one thing: re-asking within a chat, losing a conversation at handoff, forgetting a returning customer, dropping an uploaded photo, and missing what the whole company already knows are five *different* gaps, each with its own mechanism. **Short-term memory is given to you by the framework; every long-term layer is a write policy plus a recall policy that you choose.** This lab climbs those layers one at a time:

![the four memories of an agent, and where each one lives on Google Cloud](https://storage.googleapis.com/support-memory-lab-assets/img/four-memories.png)

![Maya's road, station by station — and the desk where Iris waits](https://storage.googleapis.com/support-memory-lab-assets/img/roadmap-felt.png)

You play the support lead at **Lumen & Co.**, a smart-lamp company. Your agent is **Iris**. Your customer is **Maya**, and her LumenGlow v2 flickers.

| | | | |
|:--:|---|:--:|---|
| ![Iris](https://storage.googleapis.com/support-memory-lab-assets/img/avatar-iris.png) | **Iris** — the support agent you're fixing | ![Maya](https://storage.googleapis.com/support-memory-lab-assets/img/avatar-maya.png) | **Maya** — the customer holding a cracked lamp |

Iris starts the lab with all five failures in place — *mechanically*, because the code for remembering isn't written yet. **You will write it.** Every rung repeats the same loop: run the broken behavior and watch it with your own eyes → open the file (`cloudshell edit`) → delete a `# TODO: ` prefix so the one line that is the whole lesson goes live → relaunch `adk web` → same prompts, different world. Commands in this lab are the real commands; when a setup script runs, the codelab lists exactly what it did.

### What you'll learn

`tool_context.state` · `LongRunningFunctionTool` and `FunctionResponse` · `add_session_to_memory` / `search_memory` · connecting **Vertex AI Memory Bank** · `save_artifact` · governed graph traversals — and the ideas behind them: two channels, parked runs, filed-is-not-remembered, extract-then-store, similar-is-not-connected.

### Prerequisites

You've built an agent before (tools, a runner). A Google Cloud project with billing. Everything runs in **Cloud Shell** — nothing to install on your machine.

<!-- ------------------------ -->

## Setup
Duration: 8:00

### Configure your environment

👉💻 In Cloud Shell, export the environment variables (replace `PROJECT_ID` with yours):

```bash
export GOOGLE_GENAI_USE_VERTEXAI=True
export GOOGLE_CLOUD_PROJECT="PROJECT_ID"
export GOOGLE_CLOUD_LOCATION=global
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

> aside positive
> **Why `global` and not a region?** Gemini on Vertex can serve from dynamic shared quota — a single busy region can answer `429 RESOURCE_EXHAUSTED` through no fault of yours; `global` draws on capacity across regions. If a 429 still slips through, wait a few seconds and re-run.

### Clone and run setup

👉💻

```bash
cd ~
git clone https://github.com/cuppibla/support-memory-lab.git
cd ~/support-memory-lab
./setup_cloudshell.sh
```

The script prints each step as it runs. What it does, in order:

| | |
|---|---|
| **API** | enables `aiplatform.googleapis.com` — one `gcloud services enable` |
| **virtualenv** | creates `.venv` and installs the pinned `google-adk[db,gcp]==2.7.1` |
| **auth** | writes `.env` in Vertex mode — **no API key anywhere**; Cloud Shell's own credentials do the talking (`cat .env` — three lines, that's the whole auth story) |
| **model check** | `doctor.py` makes one real Gemini call, so a broken project fails HERE, not in rung 3 |

👀 *Wait for the green checks and* `🎉 ready`.

> aside negative
> **⚠️ A new terminal tab starts deactivated.** If you ever see `adk: command not found`, run `source ~/support-memory-lab/.venv/bin/activate` in that tab. Every command block below includes it, so blocks are safe to paste into any tab.

<!-- ------------------------ -->

## Rung 1 — "What was your order number again?"
Duration: 15:00

![which memory this chapter teaches, how long it lives, what shape it is, where it sits](https://storage.googleapis.com/support-memory-lab-assets/img/locator-r1.png)

*Two channels inside one conversation: the transcript the model reads, and the state your code trusts.*

**The failure:** nothing Maya says becomes anything your code can use.
**The line you'll write:** the state write — the single line that separates a chat from a system.

### Launch adk web

👉💻 This is the command you'll use all lab long. Read the flags before you run them — two of them ARE the curriculum:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

- `--session_service_uri "sqlite:///lumen.db"` — this constructs a **SessionService**, the ADK component that decides WHERE conversations live: `sqlite://` builds a `SqliteSessionService` over a real file (the family also includes `DatabaseSessionService` for Postgres/Cloud SQL and `VertexAiSessionService` for managed sessions). This rung ends by flipping this flag; rung 2 exists because of it.
- `--artifact_service_uri "file://$PWD/artifacts_store"` — uploaded files get a real directory. Rung 4's whole plot.
- `--allow_origins="*"` — **not optional in Cloud Shell**: Web Preview proxies you through an `https://8000-…cloudshell.dev` origin the server would otherwise reject, and the UI fails in confusing ways (empty agent list is the classic symptom).

Behind these flags, adk web builds a **Runner** for each agent folder — ADK's engine, whose one job is `run_async(user_id, session_id, new_message)`: run the agent one turn against the wired services. You'll open a Runner you can actually read in the interlude after rung 2.

👉🌐 Open it via **Web Preview → Change port → 8000** (the Web Preview button sits top-right of the Cloud Shell toolbar). The **ADK dev UI** opens — you'll learn its parts as you need them.

### First, run it broken

👉🌐 In the dev UI, pick **`r1_short_term`** from the agent dropdown (top-left). Copy the block below, paste it into the message box at the bottom, and press the **➤ send** button (don't rely on Enter):

```
Hi, my lamp keeps flickering. Order number is 8841, it's a LumenGlow v2.
```

Three `update_ticket` chips appear in the feed — ⚡ means the call fired, ✓ means the response came back. The tool ran three times! **Chips are clickable:** click any ✓ chip and the event detail opens with the actual response JSON — `"status": "success"`. Everything *looks* fine.

Now open the side panel's **State** tab (the `Info · State · Artifacts · Evals` strip on the left). **Empty.** Then ask the follow-up:

```
Quick check - what order number do you have for me, and which lamp is it?
```

Iris answers correctly — *8841, LumenGlow v2*. Wait. If state is empty, how?

![r1 broken: every chip succeeded, and the State tab holds nothing your code can use](https://storage.googleapis.com/support-memory-lab-assets/img/r1-broken-state-empty.png)

**Because the transcript is still in the context window.** Within one session, the model can chat from raw history. That's what makes this bug invisible in demos and fatal in production: the *model* remembers prose, but your *code* — the part that files tickets, issues refunds, routes escalations — has nothing. No field to read. No value to act on.

### Open the file and fix it

👉💻 Press **Ctrl-C** in the adk web terminal to stop the server, then open the file:

```bash
cloudshell edit ~/support-memory-lab/r1_short_term/tools.py
```

Read `update_ticket`. It computes the key, builds the response… and the one line that would store anything is switched off:

```python
    key = f"ticket_{field}"
    # ── YOUR LINE ─ delete the "# TODO: " prefix ──────────────────────────
    # TODO: tool_context.state[key] = value
    return {"status": "success", "written": {key: value}}
```

👉📝 **Your line:** delete the `# TODO: ` prefix so it reads `tool_context.state[key] = value`. Writing through the tool context makes ADK record the change as part of the event, so it lands on disk with everything else.

👉💻 Relaunch the server:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

👉🌐 Reload the Web Preview tab (it opens a fresh session) and repeat the same two prompts.

👀 Same chips — but now a `State:` chip appears in the feed, and the **State** tab fills: `ticket_order_number: 8841`, `ticket_product`, `ticket_symptom`. The transcript is the model's channel; state is *yours*. One line of code created the second channel.

![r1 fixed: same conversation, and now the State tab holds the ticket](https://storage.googleapis.com/support-memory-lab-assets/img/r1-fixed-state.png)

> aside positive
> **On your own agent:** any fact you'll need to *act* on — an ID, an amount, a decision — belongs in state the moment it appears. Prompt-stuffing ("remember the order number!") makes the model re-derive facts from prose. State makes them load-bearing. (Curious what's physically on disk? Open `cloudshell edit ~/support-memory-lab/peek.py` — 40 lines of plain SQLite, no ADK in it — then run it with `python peek.py` to dump every session's transcript AND state.)

### The cliff this rung ends on

👉💻 Stop the server (`Ctrl-C`) and relaunch it with ONE flag changed — sessions in process RAM instead of a file:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "memory://"
```

👉🌐 Reload the Web Preview tab, then click the session title in the top bar (next to **NEW SESSION**) to open the session list: **empty.** Your whole conversation is gone — it lived in the process, and the process died.

👉💻 `Ctrl-C`, relaunch with the normal command (the `sqlite:///lumen.db` one). Everything is back. The entire difference between amnesia and persistence was one URI on a command **you** typed — which raises the question rung 2 answers: *who else can read that file?*

<!-- ------------------------ -->

## Rung 2 — "Please describe your issue from the beginning."
Duration: 16:00

![which memory this chapter teaches, how long it lives, what shape it is, where it sits](https://storage.googleapis.com/support-memory-lab-assets/img/locator-r2.png)

*Only one dial moved. Persistence changes *where* the conversation lives — not what kind of memory it is.*

**The failure:** escalation exists, but no human is actually in the loop — the run never stops to wait for one.
**The lines you'll write:** the `LongRunningFunctionTool` wrapper, and the `FunctionResponse` a supervisor sends back.

### First, run it broken

👉💻 Make sure **adk web is running** — if you stopped it, relaunch:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

👉🌐 Open it via **Web Preview → Change port → 8000**. Pick **`r2_handoff`** from the agent dropdown and send:

```
This replacement lamp is broken too. I want an $80 refund for order 8841.
```

Watch the `escalate_refund` chip: it goes ⚡→✓ **instantly, inside the same turn**, and Iris keeps talking — most likely speaking as if a review happened. Click the ✓ chip: the tool returned `"status": "pending"`… and the model just *kept going*.

**Nothing stopped it.** An ordinary tool returns and the turn rolls on — "pending" was just a word in a dict. No approval step happened, and nothing is waiting for one. Whatever Iris told Maya about a supervisor, there is no parked call anywhere for a human to find.

### Fix half one: park the run

👉💻 Press **Ctrl-C** in the adk web terminal, then open the file:

```bash
cloudshell edit ~/support-memory-lab/r2_handoff/agent.py
```

```python
# TODO: from google.adk.tools import LongRunningFunctionTool
…
escalation = escalate_refund
# TODO: escalation = LongRunningFunctionTool(escalate_refund)
root_agent = make_iris([update_ticket, escalation])
```

👉📝 **Your two lines:** delete both `# TODO: ` prefixes — the import at the top, and the wrap. A *long-running* tool tells ADK: "the real answer arrives later, from outside — do not wait, do not continue past it."

![how the parked call travels from adk web through lumen.db to a separate process and back](https://storage.googleapis.com/support-memory-lab-assets/img/parked-run.png)

👉💻 Relaunch the server:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

👉🌐 Reload the Web Preview tab and send the refund message again.

👀 The `escalate_refund` chip appears — and the turn **ends** with Iris saying a supervisor is reviewing. Nothing else happens. The run is parked, and the parked call is sitting in `lumen.db`.

![r2 parked: the turn stops at the escalation and waits](https://storage.googleapis.com/support-memory-lab-assets/img/r2-parked.png)

### Fix half two: answer the parked call

👉💻 **Keep adk web running this time** — the supervisor is the whole point of a second process. Open a **second terminal tab** (the `+` next to the terminal tabs) and open the file first — you never run a script in this lab before you've read it:

```bash
cloudshell edit ~/support-memory-lab/r2_handoff/supervisor.py
```

Read the whole file — it's the most honest 70 lines in this lab. It scans sessions for an `escalate_refund` call that was never answered, prints the full history, and sends back a `FunctionResponse` — that block is already written; read it like a sentence (the `id` names WHICH parked call, the `name` must match the tool, the `response` is what the tool finally "returns").

What's switched off is the line that makes all of it possible:

```python
    svc = None
    # ── THE WHOLE TRICK ─ delete the "# TODO: " prefix ────────────────────
    # This is the SAME file, opened with the SAME service class, that adk web
    # is using right now. That one line is why a second process can take over.
    # TODO: svc = SqliteSessionService(db_path="lumen.db")
```

👉📝 **Your line:** delete the `# TODO: ` prefix. One `SqliteSessionService(db_path="lumen.db")` — the same class, the same file the server has open — and this script can see every session, find the parked call, and answer it. **Any process that can read the session store can take over the conversation** — a CLI, a cron job, a web dashboard. You'll meet the same idea again shortly, behind an Approve button.

> aside negative
> Worth knowing: if you had run this script back when `escalate_refund` was an ordinary tool, it would have printed `no pending escalation found` — an ordinary tool leaves nothing behind for anyone to answer. Parking is what created the supervisor's job.

👉💻 Now run the script you just finished, in your second tab:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
python r2_handoff/supervisor.py
```

👀 *Expect (your history, then the prompt):*

```
⏸ PENDING: escalate_refund {'reason': 'Replacement lamp is broken.', 'amount': 80}
────────────────────────────────────────────────────────────
  [user] This replacement lamp is broken too. I want an $80 refund for order 8841.
  [iris] I'm so sorry to hear your replacement lamp is also broken. I've recorded...
────────────────────────────────────────────────────────────
Press Enter to send: APPROVED >
```

Read the history — that's the point of this whole rung — then press Enter.

```
IRIS (resumed): ...it has been approved! You should see that $80 refund in 3-5 business days.
```

👉🌐 Back in the dev UI, click the session title in the top bar and re-open your session from the list. Two new events at the bottom: the approval (sent by *your other process*) and Iris's continuation. **Maya never repeated a word.**

![r2 resumed: the reloaded session shows the approval event and the continuation](https://storage.googleapis.com/support-memory-lab-assets/img/r2-resumed.png)

> aside positive
> **The beat:** a human can only "check the chat history" if the history lives outside the process. Persistence isn't a durability feature that happens to sit near human-in-the-loop — it's the *precondition* for it. Try `python r2_handoff/supervisor.py --deny` on a fresh refund to see the other branch.

<!-- ------------------------ -->

## Interlude — the desk is already alive
Duration: 8:00

Everything rung 2 taught — persistent sessions, the parked call, the FunctionResponse — is enough to run a real product. So run it now, and keep it running for the rest of the lab.

👉💻 Open a new terminal tab for the desk backend (adk web can stay up — they use different ports):

```bash
cd ~/support-memory-lab
source .venv/bin/activate
uvicorn main:app --app-dir desk_app/backend --port 8080
```

👉💻 And one more tab for the frontend, with real npm:

```bash
cd ~/support-memory-lab/desk_app/frontend
npm install
npm run dev
```

👀 *Vite prints* `Local: http://localhost:5173/`.

👉🌐 **Web Preview → Change port → 5173.** The **Lumen Support Desk** opens: Maya's chat on the left, the supervisor's desk on the right, one status dot in the header. Type the refund request in the LEFT panel's input and press ➤:

```
This is the second broken lamp I got. I want an $80 refund for order 8841.
```

👀 The header dot turns **amber**, and the RIGHT panel lights up with an **$80 · refund · #8841** card — the full conversation underneath. Read the history first, then click **Approve**. The left panel continues on its own: refund approved, 3–5 days.

![the desk, parked: amber dot, approval card, full history for the supervisor](https://storage.googleapis.com/support-memory-lab-assets/img/desk-pending.png)

**That Approve button is your supervisor.py behind a UI** — same pending scan, same `FunctionResponse`.

### The plumbing adk web hides

This app is also the first place you can READ the machinery the flags have been constructing. 👉💻 In your work tab:

```bash
cloudshell edit ~/support-memory-lab/desk_app/backend/main.py
```

Find the block titled `the plumbing adk web hides behind flags` and read it top to bottom — four pieces, each one sentence:

```python
session_service = SqliteSessionService(db_path=str(REPO / "lumen.db"))   # WHERE conversations live
memory_service  = InMemoryMemoryService()                                # the archive (rung 3 upgrades this)
artifact_service = FileArtifactService(root_dir=REPO / "artifacts_store") # where files live
runner = Runner(agent=root_agent, app_name=APP,
                session_service=session_service,
                memory_service=memory_service,
                artifact_service=artifact_service)
```

- A **SessionService** answers *where do conversations live?* — this is literally the class your `sqlite://` flag builds.
- A **MemoryService** answers *what does the archive remember?* — in rung 3 you'll point THIS line at Memory Bank.
- An **ArtifactService** answers *where do files live?* — same directory as your `file://` flag.
- The **Runner** is ADK's engine: `run_async(user_id, session_id, new_message)` runs Iris one turn against exactly these services. adk web builds one per agent folder; this one is yours to read.

> aside positive
> The desk runs the *finished* Iris from `_solutions/` — your reference implementation, always on. As you unlock each remaining rung in adk web, come back here and try the same power in the product: recall after rung 3, the photo after rung 4, the citation path after rung 5. Web Preview can only show one port at a time — just switch between 8000 (adk web) and 5173 (the desk) as you go.

<!-- ------------------------ -->

## Rung 3 — "Welcome! How can I help you today?"
Duration: 10:00

![which memory this chapter teaches, how long it lives, what shape it is, where it sits](https://storage.googleapis.com/support-memory-lab-assets/img/locator-r3.png)

*A new kind of memory — but still inside the process, so it dies with the server. The next chapter fixes that.*

**The failure:** Maya returns a week later and Iris treats her as a stranger — while last week's session sits in the same database.
**The lines you'll write:** the write policy, the recall policy — and then the connection to **Vertex AI Memory Bank**, so the archive survives anything.

After rung 2 you might believe: "my sessions are in SQLite, so my agent has memory." This rung breaks that belief. Persistence answers *can this conversation survive?* Memory answers *can the NEXT conversation use it?* Different questions, different machinery.

### Run it broken

👉💻 Make sure **adk web is running** — if you stopped it, relaunch:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

👉🌐 Open it via **Web Preview → Change port → 8000**. Pick **`r3_last_month`** from the agent dropdown — this is *last week's* conversation:

```
My LumenGlow v2 was flickering, order 8841. The firmware update you suggested fixed it! Please close my ticket.
```

Click the ✓ `close_ticket` chip and read the response: `"filed_to_memory": false — write policy not wired yet (TODO)`. The ticket closed; nothing was archived.

👉🌐 Click **NEW SESSION** (top bar) — a week has passed:

```
Did I report a flickering LumenGlow lamp to you before?
```

Click the ✓ `recall_history` chip: `"status": "empty" — recall not wired yet (TODO)`. Iris, honestly: she has no idea.

### Write both policies

👉💻 Press **Ctrl-C** in the adk web terminal, then open the file:

```bash
cloudshell edit ~/support-memory-lab/r3_last_month/tools.py
```

Two switched-off lines, and their names are the lesson. In `close_ticket` — the **write policy** (when does a conversation become memory?):

```python
# TODO: await memory_service.add_session_to_memory(session); filed = True
```

In `recall_history` — the **recall policy** (what query searches it?):

```python
# TODO: result = await tool_context.search_memory(query)
```

👉📝 Delete both `# TODO: ` prefixes.

👉💻 Relaunch the server (same command as always):

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

👉🌐 Reload the Web Preview tab and repeat the arc: close the ticket, then click the ✓ `close_ticket` chip — the event detail opens, and the response now reads `"filed_to_memory": true`:

![clicking a chip opens the event detail — the write policy, visible](https://storage.googleapis.com/support-memory-lab-assets/img/r3-chip-json.png)

Click **NEW SESSION** — and first, ask it *vague* on purpose:

```
Have I contacted you before?
```

Iris likely comes up empty **again** — and this time it's not the TODO.

> aside negative
> **Why the vague question fails:** the local `InMemoryMemoryService` matches *keywords*. "Have I contacted you before" shares no content words with last week's transcript. Recall is a **query problem**: production services match meaning (embeddings), but "similar words ≠ the right memory" stays true at every scale — rung 5 makes it the main event.

Now with content words:

```
Did I report a flickering LumenGlow lamp to you before?
```

👀 *Expect (verified):*

```
Yes, you did! You reported a flickering LumenGlow v2 (Order #8841) previously,
which was resolved with a firmware update. Is that issue happening again?
```

![r3: a brand-new session, and Iris knows — recall_history found the filed conversation](https://storage.googleapis.com/support-memory-lab-assets/img/r3-recall.png)

The old session was in `lumen.db` the *whole time* and did nothing until you wrote a policy. Say the lab's central line out loud: **filed is not remembered.** Iris now recognizes a returning customer — two lines, both yours.

<!-- ------------------------ -->

## Deploy Memory Bank
Duration: 12:00

![which memory this chapter teaches, how long it lives, what shape it is, where it sits](https://storage.googleapis.com/support-memory-lab-assets/img/locator-membank.png)

*Same two policies, same two lines as rung 3. Only the home moved — and now it survives restarts, machines, and days.*

Rung 3's archive has one problem left, and you can trigger it yourself: 👉💻 restart the server, 👉🌐 re-ask the recall question. **Empty again.** Sessions survived (SQLite); the *archive* didn't — `InMemoryMemoryService` lives and dies with the process. This chapter deploys the managed fix: **Vertex AI Memory Bank**, hosted on an Agent Engine instance you create, verify, and connect yourself.

![deploy once, connect from anywhere, survive everything](https://storage.googleapis.com/support-memory-lab-assets/img/memory-bank.png)

### Deploy: create the instance

First look at what you're about to run — it's 10 lines and prints everything:

```bash
cloudshell edit ~/support-memory-lab/r3_last_month/create_memory_bank.py
```

One SDK call — `agent_engines.create()` — creates the **Agent Engine instance** that hosts your Memory Bank. Run it yourself (~1 minute):

👉💻 In your second terminal tab (adk web can keep running):

```bash
cd ~/support-memory-lab
source .venv/bin/activate
python r3_last_month/create_memory_bank.py
```

👀 *Expect:*

```
Done. resource: projects/…/locations/us-central1/reasoningEngines/1463…
Your AGENT_ENGINE_ID = 1463…

Next: relaunch adk web with your archive in the cloud —
add this flag to the adk web command you already know:
  --memory_service_uri "agentengine://projects/…/reasoningEngines/1463…"
```

👉💻 Verify the deployment — list your project's Agent Engine instances straight from the API:

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/$GOOGLE_CLOUD_PROJECT/locations/us-central1/reasoningEngines"
```

👀 *Expect* a `reasoningEngines` entry whose `displayName` is `support-memory-lab` — your Memory Bank's home, deployed.

👉💻 Now connect to it — `Ctrl-C` the server, then the same command **plus your new flag** (paste YOUR resource name from the output above):

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store" \
  --memory_service_uri "agentengine://PASTE_YOUR_RESOURCE_NAME"
```

Same agent code — and now every Memory Bank verb is something you already own:

| Verb | Where it lives | The line |
|---|---|---|
| **connect** | the launch command (or your own runner) | `--memory_service_uri "agentengine://…"` · `VertexAiMemoryBankService(project, location, agent_engine_id)` |
| **write** | `close_ticket` — your rung-3 write policy | `await memory_service.add_session_to_memory(session)` |
| **read** | `recall_history` — your rung-3 recall policy | `await tool_context.search_memory(query)` |

**The money shot** — 👉🌐 one more arc: close the ticket in a fresh session → **NEW SESSION** → recall (content words!) → then 👉💻 **restart the server** (`Ctrl-C`, same command with the membank flag) → 👉🌐 recall again:

**It still remembers.** The archive now outlives the process, the machine, and the day.

### The same connection, in code you own

The flag is adk web's spelling. Your own Runner spells the connection like this — and you already have one: 👉💻

```bash
cloudshell edit ~/support-memory-lab/desk_app/backend/main.py
```

Find the `AGENT_ENGINE` block — the Memory Bank configuration, exactly as the ADK docs write it:

```python
memory_service = VertexAiMemoryBankService(
    project=os.environ["GOOGLE_CLOUD_PROJECT"],      # which project
    location="us-central1",                          # where the instance lives
    agent_engine_id=AGENT_ENGINE.split("/")[-1],     # WHICH Agent Engine hosts your Memory Bank
)
```

Three parameters — project, location, agent engine id — and it drops into `Runner(memory_service=…)` in place of `InMemoryMemoryService`. Restart the desk backend with your resource name and the product's archive moves to Memory Bank too:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
AGENT_ENGINE="PASTE_YOUR_RESOURCE_NAME" uvicorn main:app --app-dir desk_app/backend --port 8080
```

> aside positive
> **The memory family, for the road:** `InMemoryMemoryService` (keyword match, dies with the process — where you started) · `VertexAiMemoryBankService` (LLM-distilled facts, semantic search, persistent — where you are now) · `VertexAiRagMemoryService` (vector search over full transcripts via a RAG corpus). All three plug into the same `Runner(memory_service=…)` slot, and your write/recall policies don't change. ADK also ships a `PreloadMemoryTool` that recalls automatically at each turn's start — this lab used an explicit tool so you could SEE recall fire as a chip.

> aside positive
> **See it in the console:** Google Cloud console → search "Agent Engine" (Vertex AI) → your `support-memory-lab` instance → Memory Bank. The facts distilled from Maya's closed tickets are inspectable there — memory you can audit outside any code.

> aside negative
> Memory Bank *distills* — it stores extracted facts, not transcripts, and consolidation is asynchronous. If a recall right after closing comes back thin, give it ~30 seconds and ask again. The phrasing will also differ from the InMemory version: you're reading distilled memory, not search hits.

<!-- ------------------------ -->

## Rung 4 — "Could you describe the damage?"
Duration: 14:00

![which memory this chapter teaches, how long it lives, what shape it is, where it sits](https://storage.googleapis.com/support-memory-lab-assets/img/locator-r4.png)

*The upload gets a home of its own; the facts you extract from it land back in short-term working state.*

**The failure:** Maya sends a photo; it influences one reply and then vanishes — no file kept, nothing searchable.
**The line you'll write:** the artifact save, in a callback that catches every upload.

### Run it broken

👉💻 Make sure **adk web is running** — if you stopped it, relaunch:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

👉🌐 Open it via **Web Preview → Change port → 8000**. Pick **`r4_the_photo`** from the agent dropdown.

First get Maya's photo onto YOUR computer — the attach dialog picks files from your machine, not from Cloud Shell. Save it from the public link:

**[https://storage.googleapis.com/support-memory-lab-assets/img/lamp_photo.jpg](https://storage.googleapis.com/support-memory-lab-assets/img/lamp_photo.jpg)** (open → right-click → Save image)

Then click the **+** (attach) button in the message box, choose the `lamp_photo.jpg` you just saved, and send:

```
Here is a photo of my broken lamp. What do you see? Please record the damage.
```

![the photo Maya sends](https://storage.googleapis.com/support-memory-lab-assets/img/lamp_photo.jpg)

👀 The moment that makes this rung — Iris reads the sticker *in the image*:

```
I've recorded that for you! I see a LumenGlow v2 from batch B7 with a crack
across the base.
```

Click the ✓ `record_damage` chip: `{"model": "LumenGlow v2", "damage": "crack across the base", "batch": "B7"}` — the model did the *seeing*, the tool recorded *what was seen*. The State tab now has `photo_model / photo_damage / photo_batch`. A supplier sticker just became queryable state.

![r4: the photo in the conversation, the batch code read off the sticker, the facts in state](https://storage.googleapis.com/support-memory-lab-assets/img/r4-photo.png)

So what's broken? 👉💻:

```bash
find ~/support-memory-lab/artifacts_store -type f
```

Nothing. The photo lived exactly as long as the message. The *facts* survived (state); the *evidence* is gone.

### Write the save

👉💻 Press **Ctrl-C** in the adk web terminal, then open the file:

```bash
cloudshell edit ~/support-memory-lab/r4_the_photo/callbacks.py
```

`stash_uploaded_photo` runs before every turn and already finds image parts in the user's message — the line that would keep them is switched off:

```python
        if blob and (blob.mime_type or "").startswith("image/"):
            # ── KEEP THE FILE ─ delete the "# TODO: " prefix ──────────────
            # TODO: await callback_context.save_artifact("user:lamp_photo.jpg", part)
            pass
```

👉📝 Delete the `# TODO: ` prefix. The `user:` prefix in the name scopes the artifact to Maya across *all* her sessions, not just this one.

👉💻 Relaunch the server:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

👉🌐 Reload the Web Preview tab, attach and send again. Then 👉💻 — a real file, saved by the `file://` artifact service your own launch command configured:

```bash
find ~/support-memory-lab/artifacts_store -type f
```

👀 *Expect:*

```
artifacts_store/apps/r4_the_photo/users/user/artifacts/lamp_photo.jpg/versions/0/lamp_photo.jpg
```

Read that path like a sentence: this artifact belongs to the **app → the user → all her sessions**, with versions. That's what the `user:` prefix bought you.

> aside negative
> The dev UI's Artifacts tab lists *session-scoped* artifacts — a `user:`-scoped file belongs to Maya, not to any one session, so it doesn't appear there. The path on disk is the truth. And the honest pattern overall: long-term memory stores are **text-first** — the artifact holds the pixels, state/memory hold the extraction, and the name ties them together. **Extract-then-store, with an artifact ref.**

<!-- ------------------------ -->

## Rung 5 — "We've never seen this issue."
Duration: 18:00

![which memory this chapter teaches, how long it lives, what shape it is, where it sits](https://storage.googleapis.com/support-memory-lab-assets/img/locator-r5.png)

*The company's records, traversed on a fixed path — the agent supplies a parameter, never a query.*

**The failure:** "never seen it" — while 37 tickets on the same batch sit in the system.
**The line you'll write:** registering the graph tool — turning institutional data into institutional *memory*.

### The world that already exists

👉💻

```bash
cloudshell edit ~/support-memory-lab/_shared/store.py
```

Read the schema: customers, orders, products, batches, tickets, defects — plain relational tables, 40 tickets seeded. **The graph is already there.** Every company's is. Nobody built a "knowledge graph"; they just ran a business.

Iris currently has ONE way to read it — run the trap.

👉💻 Make sure **adk web is running** — if you stopped it, relaunch:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

👉🌐 Open it via **Web Preview → Change port → 8000**. Pick **`r5_known_issue`** from the agent dropdown and send:

```
Search the ticket archive for other flickering lamps like mine.
```

👀 *Expect (verified):*

```
I found 40 similar tickets. Several mention the LumenGlow v2 flickering after
a firmware update, along with some reports for the LumenGlow v1 and Halo Mini.
Is your lamp one of those models?
```

![r5 trap: 40 matches across three product lines — none connected to Maya](https://storage.googleapis.com/support-memory-lab-assets/img/r5-trap.png)

Click the ✓ `search_tickets` chip and read the matches: three different product lines. Forty results, zero of which the tool can connect to *Maya*. Similar words are not relationships. This answer sounds helpful and contains nothing actionable.

### Register the graph tool

👉💻 Press **Ctrl-C** in the adk web terminal, then open the file:

```bash
cloudshell edit ~/support-memory-lab/r5_known_issue/agent.py
```

```python
root_agent = make_iris([update_ticket, LongRunningFunctionTool(escalate_refund),
                        close_ticket, recall_history, record_damage,
                        search_tickets,
                        # TODO: check_known_issue,
                        ])
```

👉📝 Delete the `# TODO: ` prefix — the tool joins the list, and its instruction rule wires itself in automatically. Before you restart — read what you just registered:

```bash
cloudshell edit ~/support-memory-lab/_shared/iris_tools.py
```

Find `check_known_issue`. It's a **fixed, parameterized SQL traversal**: order → product → batch → sibling tickets → defects, with exactly one input (`order_number`). The agent never writes the query — it calls a governed tool and quotes what comes back. (Notice `_shared/iris_agent.py` auto-wires an instruction rule for it the moment it's in the list.)

![the same tickets, read two ways: text similarity vs a governed key traversal](https://storage.googleapis.com/support-memory-lab-assets/img/similar-vs-connected.png)

👉💻 Relaunch the server:

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

👉🌐 Reload the Web Preview tab and ask:

```
Is my problem a known issue? My order number is 8841.
```

👀 *Expect (verified):*

```
It looks like your lamp is part of a batch with a known issue:
"Flicker + base crack (driver defect)".
The fix is firmware 2.1. Here is the path I found:
Maya -> order #8841 -> LumenGlow v2 -> batch B7 -> 37 tickets -> Flicker + base crack (driver defect).
```

![r5 graph: the citation path, hop by hop, ending in the fix](https://storage.googleapis.com/support-memory-lab-assets/img/r5-path.png)

Click the ✓ `check_known_issue` chip: the JSON carries `path`, `known_issue`, `fix`, `connected_tickets: 37`. That path is a **citation trail** — auditable hop by hop.

**Two beats to keep. Similar is not connected:** text search finds things that sound alike; traversal finds things that are *attached* — and support, fraud, and recommendations are usually questions about attachment. **The agent never writes the query:** one governed traversal, one parameter — deterministic, auditable, privacy-boundable, versus generating SQL against your warehouse and hoping the joins are right.

> aside positive
> **Production is one statement away.** In BigQuery, `CREATE PROPERTY GRAPH` is a zero-copy view over tables you already have. Then the same shape scales: vector search finds *where to look*, graph traversal finds *what's connected*, the model answers *with the trail*. The SQLite miniature you just wired is a faithful scale model — watch the live demo.

<!-- ------------------------ -->

## The warehouse, part 1 — the company's data
Duration: 7:00

![which memory this chapter teaches, how long it lives, what shape it is, where it sits](https://storage.googleapis.com/support-memory-lab-assets/img/locator-w1.png)

*The same records, moved into the warehouse the rest of the company already queries.*

**The failure:** rung 5's graph lived in a lab SQLite file. A real company's institutional memory lives in its **warehouse** — and your agent should read it there, not from a toy. Over three short chapters you'll load structured tables from GCS into BigQuery, generate embeddings *inside* the warehouse, and hand both to Iris as governed tools. This chapter: the data.

The Lumen world ships as plain CSVs in `warehouse/` — customers, products, batches, orders, tickets, defects. Look at one first:

👉💻 In your second terminal tab:

```bash
cloudshell edit ~/support-memory-lab/warehouse/tickets.csv
```

Three columns: `id, order_id, text`. Structured data, exactly as a support system would export it. Ship it to a bucket, then into BigQuery with **explicit schemas** — this is a warehouse, columns have names and types:

```bash
cd ~/support-memory-lab
gcloud storage buckets create gs://$GOOGLE_CLOUD_PROJECT-lumen --location=US
gcloud storage cp warehouse/*.csv gs://$GOOGLE_CLOUD_PROJECT-lumen/
bq mk --location=US --dataset lumen
```

👉💻 Now load all six tables — **run every line below** (one `bq load` per table; each prints `Waiting on bqjob_… Done`). The last argument of each is the explicit schema:

```bash
bq load --replace --source_format=CSV --skip_leading_rows=1 lumen.customers gs://$GOOGLE_CLOUD_PROJECT-lumen/customers.csv id:STRING,name:STRING
bq load --replace --source_format=CSV --skip_leading_rows=1 lumen.products  gs://$GOOGLE_CLOUD_PROJECT-lumen/products.csv  id:STRING,name:STRING
bq load --replace --source_format=CSV --skip_leading_rows=1 lumen.batches   gs://$GOOGLE_CLOUD_PROJECT-lumen/batches.csv   id:STRING,product_id:STRING
bq load --replace --source_format=CSV --skip_leading_rows=1 lumen.orders    gs://$GOOGLE_CLOUD_PROJECT-lumen/orders.csv    id:STRING,customer_id:STRING,product_id:STRING,batch_id:STRING
bq load --replace --source_format=CSV --skip_leading_rows=1 lumen.tickets   gs://$GOOGLE_CLOUD_PROJECT-lumen/tickets.csv   id:STRING,order_id:STRING,text:STRING
bq load --replace --source_format=CSV --skip_leading_rows=1 lumen.defects   gs://$GOOGLE_CLOUD_PROJECT-lumen/defects.csv   batch_id:STRING,title:STRING,fix:STRING
```

👉💻 Prove the load:

```bash
bq query --use_legacy_sql=false "SELECT COUNT(*) AS tickets FROM lumen.tickets"
```

👀 *Expect* `40`.

👉🌐 And see it with your own eyes: Google Cloud console → **BigQuery** → your project → `lumen` — six tables. Click `tickets` → **Preview**: Maya's world, as warehouse rows.

> aside positive
> **Cloud SQL instead?** The same two tools at the end of this rung work against Cloud SQL for PostgreSQL with pgvector — and `DatabaseSessionService` can put your *sessions* there too. This lab uses BigQuery because the next step happens *inside* the warehouse: no data leaves to get embedded.

<!-- ------------------------ -->

## The warehouse, part 2 — embeddings, in place
Duration: 7:00

![which memory this chapter teaches, how long it lives, what shape it is, where it sits](https://storage.googleapis.com/support-memory-lab-assets/img/locator-w2.png)

*Meaning computed beside the rows — recall that still works when no keyword matches.*

![files become tables, tables call Vertex through a connection, vectors land beside the rows](https://storage.googleapis.com/support-memory-lab-assets/img/gcs-bq-pipeline.png)

BigQuery can call Vertex AI models directly through a **connection**. Create it, find its service account, and let it call Vertex:

👉💻

```bash
bq mk --connection --location=US --connection_type=CLOUD_RESOURCE vertex_conn
bq show --connection US.vertex_conn
```

👀 The output includes a `serviceAccountId` like `bqcx-…@gcp-sa-bigquery-condel.iam.gserviceaccount.com`. Grant it (paste YOUR service account):

```bash
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="serviceAccount:PASTE_SERVICE_ACCOUNT" --role=roles/aiplatform.user --condition=None
```

Now the embedding model — one SQL statement, and the model lives in your dataset:

```bash
bq query --use_legacy_sql=false 'CREATE OR REPLACE MODEL lumen.embedder REMOTE WITH CONNECTION `US.vertex_conn` OPTIONS (ENDPOINT = "gemini-embedding-001")'
```

> aside negative
> If this answers a permission error, the IAM grant is still propagating — wait ~1 minute and run it again. Verified: it usually lands on the second try.

Embed **every ticket, in place** — no export, no pipeline:

```bash
bq query --use_legacy_sql=false 'CREATE OR REPLACE TABLE lumen.ticket_embeddings AS
SELECT id, content, ml_generate_embedding_result AS embedding
FROM ML.GENERATE_EMBEDDING(MODEL lumen.embedder, (SELECT id, text AS content FROM lumen.tickets))'
bq query --use_legacy_sql=false "SELECT COUNT(*) AS n, ARRAY_LENGTH(ANY_VALUE(embedding)) AS dims FROM lumen.ticket_embeddings"
```

👀 *Expect* `40, 3072` — forty tickets, each now a 3072-dimension vector, sitting next to the tables they came from.

### Ask the warehouse a vague question

Remember rung 3, where "Have I contacted you before?" failed because keywords didn't overlap? Watch meaning-matching handle exactly that:

```bash
bq query --use_legacy_sql=false '
SELECT base.id, base.content, ROUND(distance, 3) AS distance
FROM VECTOR_SEARCH(
  TABLE lumen.ticket_embeddings, "embedding",
  (SELECT ml_generate_embedding_result FROM ML.GENERATE_EMBEDDING(
     MODEL lumen.embedder, (SELECT "my light keeps cutting out at night" AS content))),
  top_k => 3)'
```

👀 *Expect (verified):* three `my lamp flickers sometimes in the evening` tickets — **zero shared keywords** with your query. That's the semantic entry rung 3's local memory couldn't give you.

<!-- ------------------------ -->

## The warehouse, part 3 — Iris reads it
Duration: 8:00

![which memory this chapter teaches, how long it lives, what shape it is, where it sits](https://storage.googleapis.com/support-memory-lab-assets/img/locator-w3.png)

*Both shapes, one agent: a vector search for meaning and a join for connection.*

👉💻 Read the two governed queries first:

```bash
cloudshell edit ~/support-memory-lab/r6_warehouse/tools.py
```

`warehouse_search(text)` is the VECTOR_SEARCH you just typed, parameterized. `warehouse_known_issue(order_number)` is rung 5's traversal as a BigQuery join. **The agent never writes SQL** — both queries are fixed; the model only supplies one parameter.

```bash
cloudshell edit ~/support-memory-lab/r6_warehouse/agent.py
```

```python
root_agent = make_iris([update_ticket, LongRunningFunctionTool(escalate_refund),
                        close_ticket, recall_history, record_damage,
                        warehouse_known_issue,
                        # TODO: warehouse_search,
                        ])
```

👉📝 Delete the `# TODO: ` prefix.

👉💻 Launch adk web (same command as always):

```bash
cd ~/support-memory-lab
source .venv/bin/activate
PYTHONPATH=$PWD adk web . --allow_origins="*" \
  --session_service_uri "sqlite:///lumen.db" \
  --artifact_service_uri "file://$PWD/artifacts_store"
```

👉🌐 Web Preview → port 8000 → pick **`r6_warehouse`** and send:

```
Have other customers had lamps dying on them at night?
```

👀 The `warehouse_search` chip fires — click it: the matches carry `distance` scores, and they're the evening-flicker tickets, found by *meaning*. Then:

```
Is my problem a known issue? My order number is 8841.
```

👀 The `warehouse_known_issue` chip returns the same citation path as rung 5 — `Maya -> order #8841 -> LumenGlow v2 -> batch B7 -> 37 tickets -> …` — except now it walked **BigQuery tables you loaded yourself**.

> aside positive
> The full production shape, assembled: **semantic entry finds where to look** (VECTOR_SEARCH) → **the traversal finds what's connected** (the join) → **the model answers with the trail.** Both reads live in the warehouse, next to the data — and `CREATE PROPERTY GRAPH` turns the join side into first-class graph queries when you outgrow it.

<!-- ------------------------ -->

## The desk goes to production
Duration: 8:00

You've driven Iris through a developer tool all lab long — while the product sat one port over. Time to look under its hood.

The desk has been running since the rung-2 interlude — and its Approve button has already earned its keep. Finish Maya's story in it:

👉🌐 **Web Preview → Change port → 5173** (if the servers are down, the interlude has the two commands: `uvicorn … --port 8080` and `npm run dev`).

1. Click **📎** (bottom-left) → choose the `lamp_photo.jpg` you saved in rung 4 → type `Is my problem a known issue?` → ➤.
2. Iris reads B7 off the image and quotes the citation path — inside a product UI, no dev tools anywhere.

![the desk, end of story: the photo, batch B7, and the citation trail in a product UI](https://storage.googleapis.com/support-memory-lab-assets/img/desk-trail.png)

### Read the code — it's the punchline

![three clients, one memory architecture](https://storage.googleapis.com/support-memory-lab-assets/img/arch-three-clients.png)

👉💻

```bash
cloudshell edit ~/support-memory-lab/desk_app/backend/main.py
```

~150 lines, and you've already read its plumbing twice — the Runner block in the interlude, the Memory Bank config in rung 3c. What's left is how thin the rest is:

```python
from _solutions.r5_known_issue.solution import root_agent   # same Iris
```

Scroll to `/api/approve` — recognize it? Your rung-2 pending scan and `FunctionResponse`, behind a button. `/api/chat` builds the same `Content` with an optional image part that adk web builds from the attach button. There is no memory code in the endpoints at all — the services own it.

**The UI is a client of the memory architecture, not the owner of it.** This memory design survived three different clients today: adk web, a terminal supervisor, and a React app. If yours only works inside one frontend, it's not a memory design — it's a UI feature.

> aside positive
> Where's the memory panel? There isn't one — on purpose. Users don't want the machinery; *you* do, and you have the State tab, the raw SQLite, and your cloud console. The only trace in the product is the citation path inside Iris's own reply — the one piece users actually want.

<!-- ------------------------ -->

## The support desk that remembers
Duration: 5:00

Maya's week, replayed: recorded on first mention → survived a handoff without repeating herself → recognized when she came back (even after the server died) → never re-described the damage → told, with a citation trail, that her problem was known and fixable. Five failures, five mechanisms. Every load-bearing line written by you.

![the road you just walked, precisely: eleven stops, the line you wired, the proof you saw](https://storage.googleapis.com/support-memory-lab-assets/img/roadmap-map.png)

### The decision table

| Symptom you've shipped | The fix | The line |
|---|---|---|
| Re-asks things from earlier in the chat | state, not longer prompts | `tool_context.state[k] = v` |
| Handoff (human OR restart) loses the conversation | persistent sessions | one URI on your launch command |
| Approval flows that can't pause | park the run | `LongRunningFunctionTool` + `FunctionResponse` |
| Every new chat starts from zero | write policy + recall policy | `add_session_to_memory` / `search_memory` |
| Archive dies with the process | managed memory | `--memory_service_uri "agentengine://…"` |
| Images vanish from the record | artifact + extraction | `save_artifact` in a callback |
| "Never seen this" despite the data | governed traversal | register the tool |

### Take it home: five checks for your own agent

1. Every fact you *act* on lives in state, not prose.
2. Your sessions survive `kill -9` — and something other than the chat UI can read them.
3. You can name your memory **write trigger** and **recall query** in one sentence each.
4. Anything a user uploads has an artifact home and a text extraction.
5. For questions about *connection*, you traverse — the model quotes the path, never writes the query.

### What we didn't cover (on purpose)

Context compaction and cost · `user:`/`app:` state scopes as an access-control boundary · memory that learns from outcomes (reflective memory) · evaluating recall quality. Each is its own climb.

### The line to keep

Storage is a database problem. **Memory is a surfaces-at-the-right-moment problem.** Filed is not remembered — and you've now closed that gap five different ways, with your own hands.
