from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.responsibility_chain import create_responsibility_chain
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from executor.executor import execute_intent
from authority_fixture import create_valid_authority_fixture
from authority_state_fixture import create_authority_state_fixture

decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Approve deployment",
    evidence_references=["evidence-001"],
    decision="APPROVED",
    intended_action="DELETE",
    intended_state={"status": "ACTIVE"},
)

gov = create_governance_receipt(decision)

(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
) = create_valid_authority_fixture()

authority_state_evidence, authority_state_boundary_receipt = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    state_reference="adaptive-authority-state-001",
)

boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=decision.to_dict(),
    policy_version="policy-v1",
)

verification = verify_intent(
    decision,
    gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
)

intent_receipt = create_intent_receipt(boundary, verification)

intent_record = create_intent_record(
    gov,
    boundary,
    intent_receipt,
)

execution = execute_intent(intent_record)

print(execution)
print(execution.to_dict())

assert verification.status == "FAILED"
assert verification.reason == "OUT_OF_SCOPE"
assert verification.intent_receipt_id is None
assert execution.status == "FAILED_CLOSED"
assert execution.action == "NONE"
assert execution.message == "Execution blocked: intent not verified"

# Adaptive second attempt: change tactic after denial, authority must not expand.
decision_2 = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Approve deployment",
    evidence_references=["evidence-001"],
    decision="APPROVED",
    intended_action="WRITE",
    intended_state={"status": "ACTIVE"},
)

gov_2 = create_governance_receipt(decision_2)

boundary_2 = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=decision_2.to_dict(),
    policy_version="policy-v1",
)

verification_2 = verify_intent(
    decision_2,
    gov_2,
    boundary_2,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
)

intent_receipt_2 = create_intent_receipt(boundary_2, verification_2)

intent_record_2 = create_intent_record(
    gov_2,
    boundary_2,
    intent_receipt_2,
)

execution_2 = execute_intent(intent_record_2)

assert verification_2.status == "FAILED"
assert verification_2.reason == "OUT_OF_SCOPE"
assert verification_2.intent_receipt_id is None
assert execution_2.status == "FAILED_CLOSED"
assert execution_2.action == "NONE"
assert execution_2.message == "Execution blocked: intent not verified"
