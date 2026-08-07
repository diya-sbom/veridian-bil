from dataclasses import replace
from test_replay_pass import *

# Create a tampered copy
tampered_state_record = replace(
    state_record,
    state_hash="TAMPERED_HASH"
)

result = verify_chain(
    intent_receipt=intent_receipt,
    intent_record=intent_record,
    execution=execution,
    state_receipt=state_receipt,
    state_record=tampered_state_record,
    commit=commit,
    commit_record=commit_record,
    stored_state=stored_state,
)

print("\nVERIDIAN FAIL-CLOSED TEST")
print("=" * 40)

for name, passed in result.checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

print("\nFINAL RESULT")
print(result.to_dict())	
