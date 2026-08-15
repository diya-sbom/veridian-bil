import json

from test_replay_pass import (
    intent_receipt,
    intent_record,
    execution,
    state_receipt,
    state_record,
    commit,
    commit_record,
    stored_state,
)

bundle = {
    "intent_receipt": intent_receipt.to_dict(),
    "intent_record": intent_record.to_dict(),
    "execution": execution.to_dict(),
    "state_receipt": state_receipt.to_dict(),
    "state_record": state_record.to_dict(),
    "commit": commit.to_dict(),
    "commit_record": commit_record.to_dict(),
    "stored_state": stored_state,
}

with open("validation/v008_evidence_bundle.json", "w") as f:
    json.dump(bundle, f, sort_keys=True, indent=2)

print("V-008 PRODUCER: EVIDENCE PERSISTED")
