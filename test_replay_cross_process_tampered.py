import json

from decisionassure.intent_receipt import IntentReceipt
from bil.intent_record import IntentRecord
from executor.executor import ExecutionResult
from mira.state_receipt import StateReceipt
from bil.state_record import StateRecord
from afs.commit import CommitReceipt
from bil.commit_record import CommitRecord
from replay_verifier import verify_chain

with open("validation/v009_tampered_evidence_bundle.json", "r") as f:
    bundle = json.load(f)

intent_receipt = IntentReceipt(**bundle["intent_receipt"])
intent_record = IntentRecord(**bundle["intent_record"])
execution = ExecutionResult(**bundle["execution"])
state_receipt = StateReceipt(**bundle["state_receipt"])
state_record = StateRecord(**bundle["state_record"])
commit = CommitReceipt(**bundle["commit"])
commit_record = CommitRecord(**bundle["commit_record"])
stored_state = bundle["stored_state"]


result = verify_chain(
    intent_receipt=intent_receipt,
    intent_record=intent_record,
    execution=execution,
    state_receipt=state_receipt,
    state_record=state_record,
    commit=commit,
    commit_record=commit_record,
    stored_state=stored_state,
)


print("\nVERIDIAN V-009 TAMPERED CROSS-PROCESS REPLAY")
print("=" * 40)

for check_name, passed in result.checks.items():
    symbol = "PASS" if passed else "FAIL"
    print(f"{check_name}: {symbol}")

print("\nFINAL RESULT")
print("=" * 40)
print(result.to_dict())

assert result.passed is False

print("\nV-009 RESULT: PASSED — TAMPER DETECTED AND REPLAY FAILED CLOSED")


