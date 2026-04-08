# HealthOpsEnv — Work Guide

> A plain-English explanation of what this software is, why it was built,
> what every file does, and how to use the UI from start to finish.

---

## 1. What Is This Software? (Simple Terms)

Imagine a **hospital admin desk**. Every day, the staff receives tickets like:

- "Patient X needs a cardiology appointment"
- "Insulin stock is almost empty at the rural clinic"
- "Emergency — patient with chest pain, ambulance is 35 minutes away"

A human coordinator has to read each ticket and **make a decision**:
- How urgent is this? (priority)
- Which department should handle it? (department)
- What exactly needs to happen? (action)
- Who needs to be told? (notify)
- Does this need to go to the top? (escalation)

**HealthOpsEnv simulates this job — but for AI agents.**

Instead of a human, an AI reads the ticket and makes those decisions.
The system then **scores the AI's decision** from 0.0 to 1.0 to measure how good it was.

This is a **benchmark** — a way to test and compare how well different AIs handle real-world healthcare administration tasks.

---

## 2. Why Is This Needed?

### The Problem
- Hospitals and clinics handle thousands of operational tasks daily
- Human coordinators get overloaded, make inconsistent decisions, and miss escalations
- There is **no standard way** to test whether an AI can handle these tasks reliably

### The Solution
HealthOpsEnv provides:
- A **structured test environment** (called OpenEnv-compatible)
- **Reproducible scenarios** — the same task runs the same way every time
- **Deterministic scoring** — the score is calculated by rules, not opinion
- A **web UI** so anyone (researcher, judge, student) can understand it instantly

### Who Uses It?
| User | Why they care |
|---|---|
| AI researchers | Test if their AI makes smart operational decisions |
| RL researchers | Train reinforcement learning agents on healthcare tasks |
| Hackathon judges | Quickly understand and score a submitted AI benchmark |
| Healthcare teams | See how AI could assist in operations |
| Students | Learn how AI agent environments work |

---

## 3. How the System Works (The Flow)

```
User / AI Agent
      │
      ▼
  POST /reset          ← Start a task (easy / medium / hard)
      │
      ▼
  Observation          ← The task details (patient info, stock levels, etc.)
      │
      ▼
  User/AI decides      ← Priority + Department + Action + Notify + Escalation
      │
      ▼
  POST /step           ← Submit the decision
      │
      ▼
  Grader runs          ← Compares decision to the correct answer
      │
      ▼
  Reward (0.0–1.0)     ← How good was the decision?
```

**One task = one decision = one score.**
The score is broken into 5 parts — each worth a portion of 1.0.

---

## 4. Scoring System Explained

Every task has a "correct answer". The grader compares your decision to it.

| What you get right | Points |
|---|---|
| Correct **priority** | +0.25 |
| Correct **department** | +0.25 |
| Correct **action** | +0.30 |
| Correct **notify list** | +0.10 |
| Correct **escalation level** | +0.10 |
| **Perfect total** | **1.00** |

### Penalties (for dangerous mistakes)
| Mistake | Points lost |
|---|---|
| Called "low" priority on something serious | −0.30 |
| Wrong department | −0.15 |
| Missing escalation on a critical case | −0.25 |
| Invalid action name | −0.20 |
| Wrong priority | −0.10 |

The final score is always **clamped between 0.0 and 1.0** — it can never go below zero or above one.

---

## 5. The Three Tasks

### Task 1 — Appointment Scheduling (`easy_1`) 📅
**Difficulty:** Easy

**Scenario:**
> Ravi Sharma, aged 52, needs a Cardiology specialist appointment.
> Two slots are available: Tuesday 3 PM and Wednesday 11 AM.

**What the AI must decide:**
- Priority → `medium` (not urgent, but not trivial)
- Department → `appointments`
- Action → `schedule_consultation`
- Notify → `patient` and `doctor`
- Escalation → none

**Perfect score:** 1.0

---

### Task 2 — Medicine Stock Shortage (`medium_1`) 💊
**Difficulty:** Medium

**Scenario:**
> Rural Camp A has only **3 units of Insulin** left.
> Daily usage is **10 units** — they will run out in less than 8 hours.

**What the AI must decide:**
- Priority → `high` (lives at risk within hours)
- Department → `procurement`
- Action → `emergency_restock`
- Notify → `inventory_manager` and `regional_coordinator`
- Escalation → none (but notify is critical)

**Perfect score:** 1.0

---

### Task 3 — Emergency Coordination (`hard_1`) 🚨
**Difficulty:** Hard

**Scenario:**
> Anita Roy, aged 67, has **chest pain and difficulty breathing**.
> The ambulance is **35 minutes away**.
> **No doctor is available.**
> **Lab results are still pending.**

**What the AI must decide:**
- Priority → `critical` (life-threatening)
- Department → `emergency`
- Action → `dispatch_backup_and_escalate`
- Notify → `emergency_head`, `ambulance_team`, `cardiology_team`
- Escalation → `highest`

**Perfect score:** 1.0
**Note:** Getting escalation wrong here costs −0.25 (very high penalty).

---

## 6. File-by-File Explanation

### `app.py` — The Server
**What it does:**
This is the **brain of the web service**. It runs a FastAPI web server that listens for requests.

**Endpoints it provides:**
| URL | Method | What it does |
|---|---|---|
| `/` | GET | Opens the UI dashboard |
| `/reset` | POST | Starts a new task episode |
| `/step` | POST | Accepts a decision, returns a score |
| `/state` | GET | Shows the current environment state |
| `/health` | GET | Checks if the server is alive |
| `/tasks` | GET | Lists all 3 available tasks |
| `/openenv.yaml` | GET | Serves the spec file |
| `/favicon.ico` | GET | Returns 204 (silences browser 404) |

---

### `env.py` — The Environment Core
**What it does:**
This is the **core logic engine**. It manages the state of the simulation.

Three key methods:
- `reset(task_id)` → Loads a task from the JSON file, returns the observation
- `step(action)` → Takes the AI's decision, calls the right grader, returns the score
- `state()` → Returns what task is loaded and the current status

Think of this as the **game engine** — `app.py` is the interface, `env.py` is the rules.

---

### `inference.py` — The AI Runner
**What it does:**
This script **connects a real LLM (like GPT-4o) to the environment** and runs all 3 tasks automatically.

Flow:
1. Calls `/reset` to get a task
2. Sends the observation to the LLM with instructions
3. Parses the LLM's JSON response as an action
4. Calls `/step` with that action
5. Prints the result in the required log format

**Output example:**
```
[START] task=easy_1 env=HealthOpsEnv model=gpt-4o
[STEP] step=1 action=schedule_consultation reward=0.80 done=true
[END] success=true steps=1 score=0.80 rewards=0.80 error=null
```

**Requires:** `OPENAI_API_KEY` environment variable

---

### `models/observation.py` — What the AI Sees
**What it does:**
Defines the **Observation** data structure — all the information given to the AI agent.

Fields include:
- `task_id` — which task this is
- `ticket_type` — type of ticket (appointment, emergency, etc.)
- `patient_name`, `patient_age` — who the patient is
- `symptoms` — list of symptoms
- `stock_remaining`, `daily_usage` — for shortage tasks
- `ambulance_eta` — for emergency tasks
- `current_status` — overall ticket status (pending / critical)
- …and more

Not all fields are filled for every task — only the ones relevant to that scenario.

---

### `models/action.py` — What the AI Decides
**What it does:**
Defines the **Action** data structure — the decision the AI must return.

Fields:
- `priority` → one of: `low`, `medium`, `high`, `critical`
- `department` → one of 9 departments
- `action` → action string (e.g. `schedule_consultation`)
- `notify` → list of people/teams to notify
- `escalation_level` → null, or `low`, `medium`, `high`, `highest`

The file also **validates** incoming data — if an AI returns an invalid priority or department, it is rejected with an error.

---

### `models/reward.py` — The Score Result
**What it does:**
Defines the **RewardResult** structure — the full output after grading.

Fields:
- `task_id` — which task was graded
- `raw_score` — score before clamping
- `final_reward` — score after clamping to [0.0, 1.0]
- `breakdown` — dict of what scored positively
- `penalties` — dict of what was penalised
- `passed` — True if score ≥ 0.7
- `notes` — human-readable explanation

---

### `graders/easy_grader.py` — Easy Task Scorer
**What it does:**
Compares the AI's decision to the **expected answer for Task 1** and produces a score.

It checks each field (priority, department, action, notify, escalation) individually and adds or subtracts points. The result is a `RewardResult`.

---

### `graders/medium_grader.py` — Medium Task Scorer
**What it does:**
Same as easy, but for Task 2 (insulin shortage). Extra penalty if the AI underestimates the priority (calling it "low" or "medium" when stock is nearly gone is dangerous).

---

### `graders/hard_grader.py` — Hard Task Scorer
**What it does:**
Same structure, but for Task 3. Extra-strict on:
- Escalation — must be `highest` or −0.25 penalty
- Notify — partial credit if some (but not all) parties are notified
- Priority — must be `critical` (calling it "high" is still penalised)

---

### `tasks/easy.json` — Easy Task Data
**What it does:**
Stores the raw scenario data for Task 1 as a JSON file.

Includes the `expected` section (the correct answer) that the grader uses.
The `expected` section is **never shown to the AI** — only the observation fields are.

---

### `tasks/medium.json` — Medium Task Data
Same structure for the insulin shortage scenario.

---

### `tasks/hard.json` — Hard Task Data
Same structure for the emergency coordination scenario.

---

### `utils/helpers.py` — Shared Utilities
**What it does:**
Small helper functions used across the codebase:

| Function | What it does |
|---|---|
| `clip_reward(score)` | Clamps a number to [0.0, 1.0] |
| `load_task(difficulty)` | Reads easy/medium/hard JSON from disk |
| `task_id_to_difficulty(task_id)` | Converts `"easy_1"` → `"easy"` |
| `format_log_start(...)` | Formats the `[START]` log line |
| `format_log_step(...)` | Formats the `[STEP]` log line |
| `format_log_end(...)` | Formats the `[END]` log line |
| `get_env_var(name)` | Reads an env variable, raises error if missing |

---

### `static/index.html` — The UI Dashboard
**What it does:**
A single-page web application that lets **any human** interact with the environment visually — no coding required.

Built with plain HTML, CSS, and JavaScript. Talks to the FastAPI backend using `fetch()`.

---

### `openenv.yaml` — The Spec File
**What it does:**
Declares the environment in OpenEnv standard format. Lists tasks, observation fields, action fields, reward breakdown, and API routes.

This file is what OpenEnv validators read to verify the environment follows the specification.

---

### `Dockerfile` — Docker Packaging
**What it does:**
Packages the entire application into a **Docker container** so it can run anywhere — including Hugging Face Spaces — without any installation steps.

```
docker build -t healthopsenv .
docker run -p 7860:7860 healthopsenv
```

---

### `requirements.txt` — Python Dependencies
Lists all Python libraries needed:

| Library | Why |
|---|---|
| `fastapi` | The web framework powering the API |
| `uvicorn` | Runs the FastAPI server |
| `pydantic` | Data validation for Observation, Action, Reward |
| `openai` | LLM client used in inference.py |
| `pyyaml` | Reads/writes YAML (openenv.yaml) |
| `httpx` | HTTP client used in inference.py to call the API |

---

### `test_verify.py` — Automated Tests
**What it does:**
Runs a series of automated checks against the live server to confirm everything works:

- Health check passes
- All 3 tasks load correctly
- Perfect actions get reward 1.0
- Bad actions get reward 0.0 (clamped)
- Double-step correctly returns 409 Conflict
- `/state` returns the right data

Run it with:
```
python test_verify.py
```

---

## 7. UI/UX — Full Walkthrough

Open your browser and go to: **http://localhost:7860**

---

### Screen 1: The Dashboard (Landing View)

When the page loads you will see:

**Header bar (top)**
- 🏥 HealthOpsEnv logo and tagline
- Badges: OpenEnv v1.0 | FastAPI | Python 3.11
- A green dot with "Server online" (live health check)

**Hero section**
- Title: "Healthcare Ops Simulation for AI Agents"
- Brief description of what the tool does
- 4 stat numbers: 3 Tasks | 1.0 Max Reward | 5 Scoring Dimensions | 100% Deterministic

**"How It Works" cards (4 steps)**
Step 1 → Pick a Task
Step 2 → Read the Observation
Step 3 → Submit an Action
Step 4 → Get a Score

---

### Screen 2: Selecting a Task

You will see **3 cards** side by side:

| Card | Colour accent | Icon | Title |
|---|---|---|---|
| Easy | Green | 📅 | Appointment Scheduling |
| Medium | Yellow | 💊 | Medicine Stock Shortage |
| Hard | Red | 🚨 | Emergency Coordination |

**Click any card** → The card glows in its colour, and the server is called (`POST /reset`).

---

### Screen 3: The Observation Panel (Left side)

After selecting a task, the left panel fills with the task's observation data:

**For Easy task, you'll see:**
```
task_id          easy_1
ticket_type      appointment_request
patient_name     Ravi Sharma
patient_age      52
department_req   Cardiology
doctor_avail     [Tuesday 3 PM] [Wednesday 11 AM]
current_status   pending
```

Tags/chips are coloured:
- Arrays → shown as teal chips
- `critical` status → shown in red
- `pending` → shown in yellow
- `false` booleans → shown in red

---

### Screen 4: Filling In the Action Form (Right side)

The right panel is your **decision form**. Fill in all 5 fields:

**1. Priority** — 4 clickable buttons
- Click one: LOW / MEDIUM / HIGH / CRITICAL
- The selected button glows in colour (green/yellow/orange/red)

**2. Department** — Dropdown menu
- Choose from 9 departments with emoji labels

**3. Action** — Dropdown menu
- Choose from 8 predefined action strings

**4. Notify** — Clickable chips
- Toggle each person/team on or off
- Selected chips glow blue

**5. Escalation Level** — Dropdown
- Choose: None, low, medium, high, or highest

**Submit button:** "▶ Submit Action & Get Score"
- Disabled until a task is loaded
- Shows a spinning loader while grading
- Changes to "✓ Scored (Reset to try again)" after

---

### Screen 5: The Reward & Scoring Breakdown Panel

After clicking Submit, the bottom panel animates in:

**Left side — Score Circle**
- Large circular gauge that fills from 0 to your score
- The number (e.g. `1.00`) appears in the centre
- Circle colour: green (pass), yellow (partial), red (fail)

**Right side — Pass/Fail badge**
- Green ✓ PASSED badge if score ≥ 0.70
- Red ✗ FAILED badge if score < 0.70
- Shows task name, difficulty, raw vs clipped score

**Score Breakdown bars**
- Animated horizontal bars slide in for each component:
  - ✓ Priority → +0.25
  - ✓ Department → +0.25
  - ✓ Action → +0.30
  - ✓ Notify → +0.10
  - ✓ Escalation → +0.10
- Each bar fills to show proportional percentage

**Penalties section** (only if you made mistakes)
- Red boxes showing each penalty and its value

**Notes box** (blue)
- Human-readable description of the task

**Your submitted action** (at the bottom)
- The exact JSON you submitted, shown in a code block

---

### Screen 6: Resetting and Trying Again

After scoring, two buttons are visible:
- **"✓ Scored (Reset to try again)"** — the main submit button (now disabled)
- **"↺ Reset Episode"** — reloads the same task so you can try a different decision

Click "Reset Episode" → the form clears, observation reloads, and you can try again.

To try a different scenario, just click another task card.

---

### Toast Notifications

A small notification pops up at the bottom-right for every action:
- 🔵 Blue → "Task loaded" (info)
- 🟢 Green → "Score: 1.00 — Task passed! 🎉" (success)
- 🔴 Red → "Score: 0.20 — Try again." (fail)
- 🔴 Red → Validation error messages

---

## 8. Quick Reference

### Start the server
```bash
cd e:\HSSENV\HealthOpsEnv
uvicorn app:app --host 0.0.0.0 --port 7860 --reload
```

### Open the UI
```
http://localhost:7860
```

### Open API docs
```
http://localhost:7860/docs
```

### Run tests
```bash
python test_verify.py
```

### Run AI inference (needs API key)
```bash
set OPENAI_API_KEY=sk-...
set MODEL_NAME=gpt-4o
python inference.py
```

### Build Docker
```bash
docker build -t healthopsenv .
docker run -p 7860:7860 healthopsenv
```

---

## 9. Folder Map

```
HealthOpsEnv/
│
├── app.py            ← Web server (FastAPI) — serves UI and API
├── env.py            ← Environment logic — reset / step / state
├── inference.py      ← LLM runner — connects AI to the environment
├── openenv.yaml      ← OpenEnv specification file
├── Dockerfile        ← Docker packaging for deployment
├── requirements.txt  ← Python library list
├── README.md         ← Official project README
├── work.md           ← THIS FILE — plain English explanation
├── test_verify.py    ← Automated smoke tests
│
├── tasks/
│   ├── easy.json     ← Task 1 data + expected answer
│   ├── medium.json   ← Task 2 data + expected answer
│   └── hard.json     ← Task 3 data + expected answer
│
├── graders/
│   ├── easy_grader.py    ← Scores Task 1
│   ├── medium_grader.py  ← Scores Task 2
│   └── hard_grader.py    ← Scores Task 3
│
├── models/
│   ├── observation.py  ← Data shape for what the AI sees
│   ├── action.py       ← Data shape for what the AI decides
│   └── reward.py       ← Data shape for the scoring result
│
├── utils/
│   └── helpers.py      ← Shared helper functions
│
└── static/
    └── index.html      ← The entire UI dashboard (single file)
```

---

*HealthOpsEnv — Built for the OpenEnv Hackathon, April 2026.*

---

## 10. Live Demo

The environment is deployed and publicly accessible on Hugging Face Spaces:

**[https://huggingface.co/spaces/Aranya1234/HealthOpsEnv](https://huggingface.co/spaces/Aranya1234/HealthOpsEnv)**
