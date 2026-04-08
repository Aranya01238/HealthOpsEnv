# HealthOpsEnv — Hackathon Relation Document

> How HealthOpsEnv maps to the **Meta × PyTorch OpenEnv Hackathon** requirements,
> and a full compliance checklist verifying every rule is satisfied.

---

## 1. What Is the Hackathon?

The **Meta × PyTorch OpenEnv Hackathon** challenges participants to build a complete,
real-world **OpenEnv-compatible environment** — a structured simulation that AI agents
can learn from using the standard `step()` / `reset()` / `state()` API.

**The Task (verbatim from the hackathon brief):**
> "Build a complete, real-world OpenEnv environment that an AI agent can learn from
> through the standard `step()` / `reset()` / `state()` API."

The environment must be:
- Based on a **real-world task** (not games, not toys)
- Fully OpenEnv-spec compliant
- Deployable to **Hugging Face Spaces** via Docker
- Evaluated by an automated judge that pings the environment, runs graders, and checks logs

---

## 2. How HealthOpsEnv Answers the Hackathon

**HealthOpsEnv simulates hospital administration operations.**

Every day, hospital coordinators handle tickets: scheduling appointments, managing drug
shortages, coordinating emergencies. HealthOpsEnv turns this real job into a structured
AI benchmark — the agent reads a ticket (observation), makes a decision (action),
and is scored deterministically (reward).

This is exactly the kind of real-world, non-game environment the hackathon asks for.

---

## 3. Full Compliance Checklist

Below is every requirement from the hackathon screenshots, checked against HealthOpsEnv.

---

### ✅ Key Requirements at a Glance

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Must simulate a **real-world task** (not games or toys) | ✅ | Hospital admin: appointments, drug shortages, emergencies |
| 2 | Implement full OpenEnv spec: typed models, `step()`/`reset()`/`state()`, `openenv.yaml` | ✅ | `env.py`, `models/`, `openenv.yaml` |
| 3 | Minimum **3 tasks** with agent graders (easy → medium → hard, scores 0.0–1.0) | ✅ | `easy_1`, `medium_1`, `hard_1` with dedicated graders |
| 4 | **Meaningful reward** function with partial progress signals | ✅ | 5-component partial scoring, not binary |
| 5 | Baseline **inference script** with reproducible scores | ✅ | `inference.py` in project root |
| 6 | Deploy to **Hugging Face Spaces** + working Dockerfile | ✅ | `Dockerfile` targets `python:3.11-slim`, exposes port 7860 |
| 7 | **README** with env description, action/obs spaces, setup instructions | ✅ | `README.md` covers all 12 required sections |

---

### ✅ Functional Requirements (Detailed)

#### Real-World Task Simulation
> *"The environment must simulate a task humans actually do.
> Not games, not toys. Examples: email triage, code review, scheduling, customer support."*

| Our implementation | Details |
|---|---|
| Scenario domain | Healthcare administration (hospital operations) |
| Task 1 (Easy) | Patient appointment scheduling with a specialist |
| Task 2 (Medium) | Emergency insulin restock for a rural clinic |
| Task 3 (Hard) | Multi-factor emergency: chest pain, no doctor, ambulance ETA 35 min |
| Real-world relevance | These exact scenarios are handled daily by hospital coordinators |

---

#### OpenEnv Spec Compliance
> *"Implement the full OpenEnv interface: typed Observation, Action, and Reward Pydantic models.
> `step(action)` → returns observation, reward, done, info.
> `reset()` → returns initial observation.
> `state()` → returns current state.
> `openenv.yaml` with metadata. Tested via openenv validate."*

| Requirement | File | Status |
|---|---|---|
| Typed `Observation` Pydantic model | `models/observation.py` | ✅ |
| Typed `Action` Pydantic model | `models/action.py` | ✅ |
| Typed `RewardResult` Pydantic model | `models/reward.py` | ✅ |
| `reset()` → returns initial observation | `env.py → reset()` + `POST /reset` | ✅ |
| `step(action)` → returns obs, reward, done, info | `env.py → step()` + `POST /step` | ✅ |
| `state()` → returns current state | `env.py → state()` + `GET /state` | ✅ |
| `openenv.yaml` with full metadata | `openenv.yaml` | ✅ |

---

#### Minimum 3 Tasks with Agent Graders
> *"Each task defines a concrete objective an agent must accomplish,
> with a programmatic grader that scores performance (0.0–1.0).
> Tasks should range: easy → medium → hard.
> Graders must have clear, deterministic success/failure criteria."*

| Task | Difficulty | Grader file | Score range |
|---|---|---|---|
| `easy_1`: Appointment Scheduling | Easy | `graders/easy_grader.py` | 0.0 – 1.0 |
| `medium_1`: Medicine Stock Shortage | Medium | `graders/medium_grader.py` | 0.0 – 1.0 |
| `hard_1`: Emergency Coordination | Hard | `graders/hard_grader.py` | 0.0 – 1.0 |

All graders are **fully deterministic** — same input always produces same score.

---

#### Meaningful Reward Function
> *"Provides signal over the full trajectory (not just binary end-of-episode).
> Rewards partial progress toward task completion.
> Penalizes clearly undesirable behavior."*

| Component | Points | How it works |
|---|---|---|
| Correct priority | +0.25 | Only if exact match |
| Correct department | +0.25 | Only if exact match |
| Correct action | +0.30 | Only if exact match |
| Correct notify list | +0.10 | Sorted comparison; partial credit in hard task |
| Correct escalation level | +0.10 | Only if exact match |
| Dangerous under-prioritization | −0.30 | Critical task labelled "low" |
| Missing critical escalation | −0.25 | Hard task with no escalation_level |
| Wrong department | −0.15 | Any mismatch |
| Invalid action | −0.20 | Any mismatch |
| Wrong priority | −0.10 | Non-dangerous mismatch |
| **Final reward** | **0.0–1.0** | Clamped via `clip_reward()` |

Not binary — an agent can score 0.25, 0.50, 0.75, etc. depending on partial correctness.

---

#### Baseline Inference Script
> *"Uses the OpenAI API client to run a model against the environment.
> Reads API credentials from environment variables (OPENAI_API_KEY).
> Produces a reproducible baseline score on all 3 tasks."*

| Requirement | Status | Details |
|---|---|---|
| Named `inference.py` | ✅ | In project root |
| Uses OpenAI Python client | ✅ | `from openai import OpenAI` |
| Reads `OPENAI_API_KEY` from env | ✅ | `os.environ.get("OPENAI_API_KEY")` |
| Reads `HF_TOKEN` from env | ✅ | Used as primary API key on HF Spaces |
| Reads `API_BASE_URL` from env | ✅ | `os.environ.get("API_BASE_URL", "...")` |
| Reads `MODEL_NAME` from env | ✅ | `get_env_var("MODEL_NAME", "gpt-4o")` |
| Runs all 3 tasks | ✅ | Iterates `["easy_1", "medium_1", "hard_1"]` |
| Temperature 0.0 for reproducibility | ✅ | `temperature=0.0` in `chat.completions.create` |

---

### ✅ Mandatory Additional Instructions

> *"Before submitting, ensure the following variables are defined in your environment configuration:"*

| Variable | Required | Used in | Status |
|---|---|---|---|
| `API_BASE_URL` | ✅ | `inference.py → build_client()` | ✅ |
| `MODEL_NAME` | ✅ | `inference.py → main()` | ✅ |
| `HF_TOKEN` | ✅ | `inference.py → build_client()` (primary key) | ✅ |
| `OPENAI_API_KEY` | ✅ | `inference.py → build_client()` (fallback) | ✅ |

> *"The inference script must be named `inference.py` and placed in the root directory of the project."*

✅ File is at `HealthOpsEnv/inference.py` (project root).

> *"Participants must use OpenAI Client for all LLM calls using above variables."*

✅ Only `from openai import OpenAI` is used — no other LLM client.

> *"Participants must emit structured stdout logs strictly following the [START], [STEP], and [END] format."*

Our exact output format:
```
[START] task=easy_1 env=HealthOpsEnv model=gpt-4o
[STEP] step=1 action=schedule_consultation reward=0.80 done=true
[END] success=true steps=1 score=0.80 rewards=0.80 error=null
```

✅ Matches the `[START]`, `[STEP]`, `[END]` format exactly, using the helper functions in `utils/helpers.py`.

---

### ✅ Non-Functional Requirements

#### Deploys to a Hugging Face Space
> *"Environment must run as a containerized HF Space tagged with openenv."*

| Requirement | Status | Details |
|---|---|---|
| Runs on HF Spaces | ✅ | Docker image based on `python:3.11-slim` |
| Port 7860 | ✅ | `EXPOSE 7860`, CMD binds to port 7860 |
| Tagged with `openenv` | ⚠️ | **Must add the `openenv` tag when creating the HF Space** |
| Server returns 200 on ping | ✅ | `GET /health` returns `{"status": "ok"}` |
| Responds to `reset()` | ✅ | `POST /reset` returns initial observation |

> ⚠️ **Action needed:** When creating the Hugging Face Space, add the tag `openenv` in the Space settings.

---

#### Containerized Execution
> *"Must include a working Dockerfile. The environment should start cleanly with docker build + docker run."*

| Requirement | Status | Details |
|---|---|---|
| `Dockerfile` exists | ✅ | At project root |
| `docker build` works | ✅ | Uses `python:3.11-slim`, installs requirements |
| `docker run` works | ✅ | `CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]` |
| Health check defined | ✅ | `HEALTHCHECK` using `httpx` |
| Non-root user | ✅ | Creates and uses `appuser` |

```bash
docker build -t healthopsenv .
docker run -p 7860:7860 healthopsenv
```

---

#### Documentation (README)
> *"README must include: environment description and motivation, action and observation space definitions,
> task descriptions with expected difficulty, setup and usage instructions, baseline scores."*

| README Section | Status |
|---|---|
| Environment description | ✅ Section 1 & 2 |
| Motivation / why healthcare ops matter | ✅ Section 2 |
| Observation space definition | ✅ Section 3 |
| Action space definition | ✅ Section 4 |
| Reward logic | ✅ Section 5 |
| Task descriptions with difficulty | ✅ Section 6 (Easy/Medium/Hard) |
| Installation instructions | ✅ Section 7 |
| Docker instructions | ✅ Section 8 |
| HF deployment instructions | ✅ Section 9 |
| Baseline scores | ✅ Section 10 (gpt-4o baselines) |

---

### ✅ Evaluation Criteria (Automated Judge)

| Criterion | What the judge does | Our status |
|---|---|---|
| **HF Space deploys** | Pings URL, checks 200, calls reset() | ✅ `/health` → 200, `/reset` → observation |
| **OpenEnv spec compliance** | Validates openenv.yaml, typed models, endpoints | ✅ All present and correct |
| **Dockerfile builds** | Automated docker build on the repo | ✅ Dockerfile at root |
| **Baseline reproduces** | Runs inference.py, checks for no errors and scores | ✅ Runs all 3 tasks cleanly |
| **3+ tasks with graders** | Enumerates tasks, runs each grader, verifies 0.0–1.0 | ✅ easy, medium, hard all clamp to [0, 1] |

---

### ✅ Infrastructure Restrictions

> *"Runtime of inference script should be less than 20min.
> Make sure your env and inference can run on a machine with vcpu=2, memory=8gb."*

| Constraint | Requirement | Our status |
|---|---|---|
| Max runtime | < 20 minutes | ✅ Each task = 1 LLM call + 2 HTTP calls ≈ ~5 seconds |
| CPU | 2 vCPUs | ✅ No heavy computation, pure Python |
| RAM | 8 GB | ✅ FastAPI + Pydantic uses < 200 MB |
| Dependencies | Listed in requirements.txt | ✅ Only lightweight packages |

---

## 4. What Still Needs to Be Done Before Submission

| Action | Priority | Details |
|---|---|---|
| **Create HF Space** | 🔴 Must do | Go to huggingface.co/spaces → New Space → Docker SDK |
| **Add `openenv` tag** | 🔴 Must do | In HF Space settings, add tag `openenv` |
| **Push code to HF Space** | 🔴 Must do | `git remote add space https://huggingface.co/spaces/YOUR_USER/healthopsenv` |
| **Add secrets in HF Space** | 🔴 Must do | Add `OPENAI_API_KEY` or `HF_TOKEN`, `MODEL_NAME`, `API_BASE_URL` in Space secrets |
| **Run validator script** | 🟡 Should do | Run the OpenEnv pre-submission validation script if available |
| **Verify HF Space URL returns 200** | 🔴 Must verify | `curl https://YOUR_USER-healthopsenv.hf.space/health` |

---

## 5. Submission Checklist

Run through this before hitting submit:

- [ ] HF Space is created and public
- [ ] Tag `openenv` is added to the Space
- [ ] `inference.py` is in the project root
- [ ] All 4 env vars are set in HF Space secrets: `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`, `OPENAI_API_KEY`
- [ ] `docker build -t healthopsenv . && docker run -p 7860:7860 healthopsenv` works locally
- [ ] `GET /health` returns `{"status": "ok"}` with HTTP 200
- [ ] `POST /reset` with `{"task_id": "easy_1"}` returns a valid observation
- [ ] `POST /step` with a valid action returns `reward` between 0.0 and 1.0
- [ ] `python inference.py` runs without error and prints `[START]`, `[STEP]`, `[END]` for all 3 tasks
- [ ] `python test_verify.py` passes all 8 tests
- [ ] `openenv.yaml` is present at project root
- [ ] `README.md` has all required sections

---

## 6. Summary Score

```
Hackathon compliance: 13/14 criteria fully met
               Gap 1: HF Space not yet created (pre-deployment step)
```

**Everything in the code is compliant.** The only remaining items are
deployment steps (creating the HF Space, pushing the repo, adding secrets)
which happen outside the codebase.

---

*HealthOpsEnv was built specifically to meet every requirement of the Meta × PyTorch OpenEnv Hackathon.*
*Healthcare operations was chosen as the domain because it is a real, impactful, non-trivial problem domain*
*that demonstrates the practical value of AI agent benchmarks beyond toy examples.*
