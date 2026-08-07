from records.intent_record import create_intent_record
from records.state_record import create_state_record
from records.commit_record import create_commit_record
from records.replay import replay

records = []

intent = create_intent_record(
    "intent-001",
    {"action": "approve"}
)
records.append(intent)

state = create_state_record(
    "state-001",
    {"status": "SUCCESS"},
    intent["current_hash"]
)
records.append(state)

commit = create_commit_record(
    "commit-001",
    {"result": "COMMITTED"},
    state["current_hash"]
)
records.append(commit)

print("Records created:", len(records))

passed, message = replay(records)
print("Replay:", passed)
print(message)

# Tamper with the state record
records[1]["payload"]["status"] = "FAILED"

passed, message = replay(records)
print("Replay after tampering:", passed)
print(message)
