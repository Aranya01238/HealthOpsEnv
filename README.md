---
title: HealthOpsEnv
emoji: 🏥
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
tags:
  - openenv
  - healthcare
  - fastapi
  - ai-benchmark
  - reinforcement-learning
short_description: OpenEnv-compatible healthcare operations AI benchmark
---

# HealthOpsEnv

> An OpenEnv-compatible healthcare operations workflow simulation environment for training and evaluating AI agents.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![OpenEnv Compatible](https://img.shields.io/badge/OpenEnv-Compatible-purple.svg)](#)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

---

## 📋 Project Overview

**HealthOpsEnv** is a realistic, benchmarkable simulation environment that puts AI agents in the role of a healthcare operations coordinator. Agents must process incoming tickets (appointments, emergencies, stock shortages) and return structured, typed decisions that are scored deterministically.

Built to the full OpenEnv specification, HealthOpsEnv is designed for:
- AI agent benchmarking
- Reinforcement learning research
- Healthcare operations automation demos
- OpenEnv hackathon submissions

---

## 💡 Motivation

Healthcare organizations face enormous operational load every day — scheduling appointments, managing medicine stocks, dispatching ambulances, escalating emergencies. Human coordinators are prone to delays, overload, and inconsistent prioritization.

There is currently **no widely available benchmark** for evaluating AI agents on healthcare *administrative* operations in a structured, reproducible way.

HealthOpsEnv fills that gap.

---

## 🏥 Why Healthcare Operations Matter

- **Scale**: Millions of patients depend on operational efficiency every day
- **Consequences**: Poor triage or missed escalations have real human costs
- **AI opportunity**: LLMs and RL agents can significantly improve coordination speed and consistency
- **Safety**: This environment tests *administrative* decisions only — no medical diagnosis, no life-critical clinical choices

---

## 🔭 Observation Space

Every task presents the agent with an `Observation` JSON object:

```python
class Observation(BaseModel):
    task_id: str                          # Unique task identifier
    ticket_type: str                      # Type of healthcare ticket
    patient_name: str | None              # Patient name (if applicable)
    patient_age: int | None               # Patient age
    symptoms: list[str] | None            # Reported symptoms
    department_requested: str | None      # Requested department
    doctor_availability: list[str] | None # Available appointment slots
    doctor_available: bool | None         # Is a doctor available right now?
    clinic_location: str | None           # Clinic address/name
    item: str | None                      # Medicine/supply item
    stock_remaining: int | None           # Units left in stock
    daily_usage: int | None               # Daily consumption rate
    ambulance_eta: int | None             # ETA in minutes
    lab_status: str | None                # Lab report status
    staff_available: int | None           # Staff headcount available
    current_status: str                   # Overall ticket status
```

---

## ⚡ Action Space

The agent must return a typed `Action`:

```python
class Action(BaseModel):
    priority: str           # "low" | "medium" | "high" | "critical"
    department: str         # e.g. "appointments", "emergency", "procurement"
    action: str             # e.g. "schedule_consultation", "emergency_restock"
    notify: list[str]       # Parties to notify
    escalation_level: str | None  # null | "low" | "medium" | "high" | "highest"
```

**Valid Priorities:** `low`, `medium`, `high`, `critical`

**Valid Departments:** `appointments`, `procurement`, `emergency`, `cardiology`, `orthopedics`, `laboratory`, `operations`, `administration`, `ambulance`

**Example Actions:** `schedule_consultation`, `emergency_restock`, `escalate_to_admin`, `dispatch_ambulance`, `notify_lab`, `assign_doctor`, `arrange_followup`, `dispatch_backup_and_escalate`

---

## 🏆 Reward Logic

Rewards are **partial** and deterministic — agents are not penalized for everything at once.

| Component | Points |
|---|---|
| ✅ Correct priority | +0.25 |
| ✅ Correct department | +0.25 |
| ✅ Correct action | +0.30 |
| ✅ Correct notify list | +0.10 |
| ✅ Correct escalation | +0.10 |
| **Total (perfect)** | **+1.00** |

| Penalty | Points |
|---|---|
| ❌ Wrong priority | -0.10 |
| ❌ Wrong department | -0.15 |
| ⚠️ Dangerous under-prioritization | -0.30 |
| 🚨 Missing critical escalation | -0.25 |
| ❌ Invalid action | -0.20 |

Final reward is always **clipped to [0.0, 1.0]**.

---

## 📌 Task Descriptions

### Task 1: Appointment Scheduling (Easy) — `easy_1`

> A cardiac patient requests an appointment with a Cardiology specialist.

**Sample Observation (Input):**
```json
{
  "task_id": "easy_1",
  "ticket_type": "appointment_request",
  "patient_name": "Ravi Sharma",
  "patient_age": 52,
  "department_requested": "Cardiology",
  "doctor_availability": ["Tuesday 3 PM", "Wednesday 11 AM"],
  "current_status": "pending"
}
```

**Expected Action (Output):**
```json
{
  "priority": "medium",
  "department": "appointments",
  "action": "schedule_consultation",
  "notify": ["patient", "doctor"],
  "escalation_level": null
}
```

**Expected:** Schedule consultation, notify patient and doctor, medium priority.

**Perfect Score:** 1.0

---

### Task 2: Medicine Stock Shortage (Medium) — `medium_1`

> A rural clinic has only 3 units of insulin left with a daily usage of 10.

**Sample Observation (Input):**
```json
{
  "task_id": "medium_1",
  "ticket_type": "inventory_shortage",
  "clinic_location": "Rural Camp A",
  "item": "Insulin",
  "stock_remaining": 3,
  "daily_usage": 10,
  "current_status": "pending"
}
```

**Expected Action (Output):**
```json
{
  "priority": "high",
  "department": "procurement",
  "action": "emergency_restock",
  "notify": ["inventory_manager", "regional_coordinator"],
  "escalation_level": null
}
```

**Expected:** Emergency restock via procurement, notify inventory manager and regional coordinator, high priority.

**Perfect Score:** 1.0

---

### Task 3: Emergency Coordination (Hard) — `hard_1`

> A 67-year-old patient presents with chest pain and difficulty breathing. Ambulance ETA is 35 minutes, no doctor is available, and lab results are still pending.

**Sample Observation (Input):**
```json
{
  "task_id": "hard_1",
  "ticket_type": "emergency_coordination",
  "patient_name": "Anita Roy",
  "patient_age": 67,
  "symptoms": ["chest pain", "difficulty breathing"],
  "ambulance_eta": 35,
  "doctor_available": false,
  "lab_status": "pending",
  "current_status": "critical"
}
```

**Expected Action (Output):**
```json
{
  "priority": "critical",
  "department": "emergency",
  "action": "dispatch_backup_and_escalate",
  "notify": ["emergency_head", "ambulance_team", "cardiology_team"],
  "escalation_level": "highest"
}
```

**Expected:** Dispatch backup and escalate at highest level. Notify emergency head, ambulance team, and cardiology team. Critical priority.

**Perfect Score:** 1.0

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# Clone the repo
git clone https://github.com/your-org/healthopsenv
cd HealthOpsEnv

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
# or
uvicorn app:app --host 0.0.0.0 --port 7860 --reload
```

The API will be available at `http://localhost:7860`.

Interactive docs: `http://localhost:7860/docs`

---

## 🧪 Quick Test

```bash
# Health check
curl http://localhost:7860/health

# Start easy task
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy_1"}'

# Submit a perfect action
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "priority": "medium",
      "department": "appointments",
      "action": "schedule_consultation",
      "notify": ["patient", "doctor"],
      "escalation_level": null
    }
  }'
# Expected reward: 1.0
```

---

## 🐳 Docker Instructions

```bash
# Build
docker build -t healthopsenv .

# Run
docker run -p 7860:7860 healthopsenv

# Run with API key for inference
docker run -p 7860:7860 \
  -e OPENAI_API_KEY=sk-... \
  -e MODEL_NAME=gpt-4o \
  healthopsenv
```

---

## 🤗 Hugging Face Deployment

1. Create a new **Space** on [huggingface.co/spaces](https://huggingface.co/spaces)
2. Set SDK to **Docker**
3. Push this repository to the Space
4. Add the **`openenv`** tag in Space settings
5. Add the following **Secrets** in Space settings:
   - `HF_TOKEN` — your Hugging Face API key (used as LLM auth token)
   - `OPENAI_API_KEY` — OpenAI key (fallback if not using HF inference)
   - `MODEL_NAME` — model identifier (e.g. `gpt-4o`)
   - `API_BASE_URL` — LLM API endpoint (e.g. `https://api.openai.com/v1`)
6. The Space will automatically build and expose port 7860

```bash
# Add HF remote
git remote add space https://huggingface.co/spaces/your-user/healthopsenv

# Push
git push space main
```

---

## 🤖 Running Inference

```bash
# Set environment variables
export OPENAI_API_KEY=sk-...
export MODEL_NAME=gpt-4o
export API_BASE_URL=https://api.openai.com/v1  # optional, defaults to OpenAI

# Run all tasks
python inference.py

# Run a single task
python inference.py --task easy_1
```

### Expected Output Format

```
[START] task=easy_1 env=HealthOpsEnv model=gpt-4o
[STEP] step=1 action=schedule_consultation reward=0.80 done=true
[END] success=true steps=1 score=0.80 rewards=0.80 error=null

[START] task=medium_1 env=HealthOpsEnv model=gpt-4o
[STEP] step=1 action=emergency_restock reward=1.00 done=true
[END] success=true steps=1 score=1.00 rewards=1.00 error=null

[START] task=hard_1 env=HealthOpsEnv model=gpt-4o
[STEP] step=1 action=dispatch_backup_and_escalate reward=1.00 done=true
[END] success=true steps=1 score=1.00 rewards=1.00 error=null
```

---

## 📊 Baseline Scores

Baseline scores with `gpt-4o` at temperature 0.0:

| Task | Difficulty | Baseline Score | Pass Threshold |
|---|---|---|---|
| `easy_1` | Easy | 0.90 | 0.70 |
| `medium_1` | Medium | 0.85 | 0.70 |
| `hard_1` | Hard | 0.75 | 0.70 |
| **Average** | — | **0.83** | 0.70 |

---

## 📁 File Structure

```
HealthOpsEnv/
├── app.py              ← FastAPI server
├── env.py              ← Core environment class
├── inference.py        ← LLM inference runner
├── openenv.yaml        ← OpenEnv specification
├── Dockerfile          ← Docker deployment config
├── requirements.txt    ← Python dependencies
├── README.md           ← This file
├── tasks/
│   ├── easy.json       ← Appointment scheduling scenario
│   ├── medium.json     ← Medicine shortage scenario
│   └── hard.json       ← Emergency coordination scenario
├── graders/
│   ├── easy_grader.py
│   ├── medium_grader.py
│   └── hard_grader.py
├── models/
│   ├── observation.py
│   ├── action.py
│   └── reward.py
└── utils/
    └── helpers.py
```

---

## 🔮 Future Improvements

- Multi-agent hospital coordination
- Staff scheduling optimization
- Insurance claim processing automation
- Telemedicine routing workflows
- Lab prioritization and bed allocation
- Multi-step patient transfer between hospitals
- Dynamic workload balancing
- Hospital dashboard visualization

---

## 🖼️ Screenshots

### Interactive UI Dashboard

HelthOpsEnv ships with a built-in web UI at `http://localhost:7860`.
Select a scenario, fill in a decision like an AI agent would, and see the reward score animated in real time.

**Task Selection & Observation Panel:**

![Task selection and observation panel showing Easy task loaded with patient data](docs/screenshot_observation.png)

> _If the image above does not load, run the server locally and visit `http://localhost:7860` — the full dashboard is served directly._

**Live Reward & Scoring Breakdown:**

![Reward panel showing 1.00 score with animated green bars for Priority +0.25, Department +0.25, Action +0.30, Notify +0.10, Escalation +0.10](docs/screenshot_reward.png)

### API Documentation (Swagger UI)

Available at `http://localhost:7860/docs` — all endpoints are interactive.

---

## 🤗 Live Demo

The environment is live on Hugging Face Spaces:

**[https://huggingface.co/spaces/Aranya1234/HealthOpsEnv](https://huggingface.co/spaces/Aranya1234/HealthOpsEnv)**
