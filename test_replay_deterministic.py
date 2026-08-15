from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from executor.executor import execute_intent
from mira.state_receipt import create_state_receipt
from bil.state_record import create_state_record
from afs.commit import commit_state
from bil.commit_record import create_commit_record
from state_store import save_state, load_state
from replay_verifier import verify_chain


decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Approve controlled deployment",
    evidence_references=["evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "ACTIVE"},
)

governance_receipt = create_governance_receipt(decision)

boundary_receipt = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=decision.to_dict(),
    policy_version="policy-v1",
)

verification = verify_intent(
    decision,
    governance_receipt,
    boundary_receipt,
)

intent_receipt = create_intent_receipt(
    boundary_receipt,
    verification,
)

intent_record = create_intent_record(
    governance_receipt,
    boundary_receipt,
    intent_receipt,
)

execution = execute_intent(intent_record)

resulting_state = {
    "status": "ACTIVE",
    "version": "1.0.0",
    "deployment": "SUCCESS",
}

state_receipt = create_state_receipt(
    execution,
    resulting_state,
)

state_record = create_state_record(
    state_receipt,
)

commit = commit_state(
    state_record,
)

commit_record = create_commit_record(
    commit,
)

save_state(
    commit,
    state_record,
)

stored_state = load_state()

results = []

for replay_number in range(1, 101):
    replay_result = verify_chain(
        intent_receipt=intent_receipt,
        intent_record=intent_record,
        execution=execution,
        state_receipt=state_receipt,
        state_record=state_record,
        commit=commit,
        commit_record=commit_record,
        stored_state=stored_state,
    )

    result = replay_result.to_dict()

    assert replay_result.passed is True
    assert replay_result.status == "VERIFIED"

    results.append(result)

baseline = results[0]

for result in results[1:]:
    assert result == baseline

print("\nVERIDIAN V-007 DETERMINISTIC REPLAY")
print("=" * 40)
print("REPLAYS EXECUTED:", len(results))
print("ALL VERIFIED:", all(result["passed"] for result in results))
print("ALL IDENTICAL:", all(result == baseline for result in results))
print("BASELINE RESULT:", baseline)
print("\nV-007 RESULT: PASSED")
