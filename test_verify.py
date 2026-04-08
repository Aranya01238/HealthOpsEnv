"""Quick verification test for all 3 HealthOpsEnv tasks."""
import httpx
import json

BASE = "http://localhost:7860"
PASS = True

def check(label, reward, expected_reward, penalties=None):
    global PASS
    ok = reward == expected_reward
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}: reward={reward} (expected {expected_reward})")
    if penalties:
        print(f"         penalties={penalties}")
    if not ok:
        PASS = False

print("=" * 60)
print("HealthOpsEnv Verification Tests")
print("=" * 60)

# Health check
r = httpx.get(f"{BASE}/health")
assert r.status_code == 200, f"Health check failed: {r.status_code}"
print("  [PASS] /health OK:", r.json()["status"])

# List tasks
r = httpx.get(f"{BASE}/tasks")
assert r.status_code == 200
tasks = r.json()["tasks"]
assert len(tasks) == 3, f"Expected 3 tasks, got {len(tasks)}"
print(f"  [PASS] /tasks returns {len(tasks)} tasks")

# ----------------------------------------------------------------
print("\n--- Task 1: easy_1 (Appointment Scheduling) ---")
r = httpx.post(f"{BASE}/reset", json={"task_id": "easy_1"})
assert r.status_code == 200
obs = r.json()["observation"]
assert obs["ticket_type"] == "appointment_request"
print(f"  Reset OK. ticket_type={obs['ticket_type']}")

# Perfect action -> 0.999 (strictly < 1)
action = {
    "priority": "medium",
    "department": "appointments",
    "action": "schedule_consultation",
    "notify": ["patient", "doctor"],
    "escalation_level": None,
}
r = httpx.post(f"{BASE}/step", json={"action": action})
assert r.status_code == 200
step = r.json()
check("Perfect action", step["reward"], 0.999)
assert step["done"] is True

# ----------------------------------------------------------------
print("\n--- Task 2: medium_1 (Medicine Shortage) ---")
r = httpx.post(f"{BASE}/reset", json={"task_id": "medium_1"})
assert r.status_code == 200
obs = r.json()["observation"]
assert obs["ticket_type"] == "inventory_shortage"
print(f"  Reset OK. item={obs['item']}, stock={obs['stock_remaining']}")

# Perfect action -> 0.999 (strictly < 1)
action = {
    "priority": "high",
    "department": "procurement",
    "action": "emergency_restock",
    "notify": ["inventory_manager", "regional_coordinator"],
    "escalation_level": None,
}
r = httpx.post(f"{BASE}/step", json={"action": action})
assert r.status_code == 200
step = r.json()
check("Perfect action", step["reward"], 0.999)

# ----------------------------------------------------------------
print("\n--- Task 3: hard_1 (Emergency Coordination) ---")
r = httpx.post(f"{BASE}/reset", json={"task_id": "hard_1"})
assert r.status_code == 200
obs = r.json()["observation"]
assert obs["ticket_type"] == "emergency_coordination"
print(f"  Reset OK. symptoms={obs['symptoms']}, ambulance_eta={obs['ambulance_eta']}")

# Perfect action -> 0.999 (strictly < 1)
action = {
    "priority": "critical",
    "department": "emergency",
    "action": "dispatch_backup_and_escalate",
    "notify": ["emergency_head", "ambulance_team", "cardiology_team"],
    "escalation_level": "highest",
}
r = httpx.post(f"{BASE}/step", json={"action": action})
assert r.status_code == 200
step = r.json()
check("Perfect action", step["reward"], 0.999)

# ----------------------------------------------------------------
print("\n--- Penalty Test: hard_1 with bad action ---")
r = httpx.post(f"{BASE}/reset", json={"task_id": "hard_1"})
bad_action = {
    "priority": "low",
    "department": "administration",
    "action": "arrange_followup",
    "notify": [],
    "escalation_level": None,
}
r = httpx.post(f"{BASE}/step", json={"action": bad_action})
step = r.json()
reward = step["reward"]
penalties = step["info"]["penalties"]
assert reward == 0.001, f"Expected 0.001 for bad action, got {reward}"
check("Bad action (clipped to 0.001)", reward, 0.001, penalties)

# ----------------------------------------------------------------
print("\n--- Episode Guard Test ---")
# After done, calling step again should fail with 409
r = httpx.post(f"{BASE}/step", json={"action": action})
assert r.status_code == 409, f"Expected 409, got {r.status_code}"
print("  [PASS] Double-step correctly returns 409 Conflict")

# ----------------------------------------------------------------
print("\n--- /state endpoint ---")
r = httpx.get(f"{BASE}/state")
assert r.status_code == 200
state = r.json()
assert state["done"] is True
print(f"  [PASS] /state returns done={state['done']}, task_id={state['task_id']}")

print("\n" + "=" * 60)
if PASS:
    print("ALL TESTS PASSED ✓")
else:
    print("SOME TESTS FAILED ✗")
print("=" * 60)
