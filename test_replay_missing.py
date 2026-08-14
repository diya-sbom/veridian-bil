from test_replay_pass import *
from replay_verifier import verify_chain

print("\nVERIDIAN MISSING-EVIDENCE TEST")
print("=" * 40)

try:
    result = verify_chain(
        intent_receipt=intent_receipt,
        intent_record=intent_record,
        execution=execution,
        state_receipt=None,
        state_record=state_record,
        commit=commit,
        commit_record=commit_record,
        stored_state=stored_state,
    )

    print("\nFINAL RESULT")
    print(result.to_dict())

except Exception as exc:
    print("\nVERIFIER REJECTED INCOMPLETE CHAIN")
    print(type(exc).__name__ + ":", str(exc))
