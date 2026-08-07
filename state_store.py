import json
import os


STATE_STORE_FILE = "state_store.json"


def load_state():

    if not os.path.exists(STATE_STORE_FILE):
        return {}

    with open(STATE_STORE_FILE, "r") as f:
        return json.load(f)


def save_state(commit, state_record):

    state = load_state()

    state["commit_id"] = commit.commit_id
    state["execution_id"] = commit.execution_id
    state["state_record_id"] = state_record.state_record_id
    state["state_hash"] = state_record.state_hash
    state["verification_status"] = state_record.verification_status
    state["committed"] = commit.committed

    with open(STATE_STORE_FILE, "w") as f:
        json.dump(state, f, indent=4)

    return state
