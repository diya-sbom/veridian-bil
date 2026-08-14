from dataclasses import replace
from test_replay_pass import *
from replay_verifier import verify_chain

tampered_state = dict(state_receipt.state)
tampered_state["status"] = "TAMPERED"

tampered_state_receipt = replace(
    state_receipt,
    state=tampered_state,
)

print("\nVERIDIAN TAMPERED-EVIDENCE TEST")
print("=" * 40)

try:
    result = verify_chain(
        intent_receipt=intent_receipt,
        intent_record=intent_record,
        execution=execution,
        state_receipt=tampered_state_receipt,
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
