from dataclasses import replace

from test_replay_pass import *
from replay_verifier import verify_chain


# Start with an otherwise-valid verified IntentRecord.
# Change ONLY the action that the record claims Diya authorized.
# Do not recompute the original artifact hash or signature.
tampered_intent_record = replace(
    intent_record,
    verified_action="EXECUTE_PAYMENT",
)

print("\nVERIDIAN VERIFIED-ACTION TAMPER TEST")
print("=" * 44)
print("ORIGINAL ACTION:", intent_record.verified_action)
print("TAMPERED ACTION:", tampered_intent_record.verified_action)

result = verify_chain(
    intent_receipt=intent_receipt,
    intent_record=tampered_intent_record,
    execution=execution,
    state_receipt=state_receipt,
    state_record=state_record,
    commit=commit,
    commit_record=commit_record,
    stored_state=stored_state,
)

data = result.to_dict()

print("\nFINAL RESULT")
print(data)

assert data["passed"] is False
assert data["status"] == "FAILED_CLOSED"

# The changed action is covered by the IntentRecord hash/signature.
assert data["checks"]["intent_record_hash"] is False
assert data["checks"]["intent_record_signature"] is False

# The IntentRecord action must also remain bound to the IntentReceipt action.
assert data["checks"]["intent_linkage"] is False

print(
    "PASS: verified action tampering detected; "
    "replay failed closed"
)
