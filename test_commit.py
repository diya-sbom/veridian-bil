from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.responsibility_chain import create_responsibility_chain
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from executor.executor import _execute_verified_intent
from mira.state_receipt import create_state_receipt
from bil.state_record import create_state_record
from afs.commit import commit_state
from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture

decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Approve deployment",
    evidence_references=["evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "ACTIVE"},
)

gov = create_governance_receipt(decision)

(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture()

authority_state_evidence, authority_state_boundary_receipt = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
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
    trusted_key_registry=trusted_key_registry)

intent_receipt = create_intent_receipt(
    boundary,
    verification,
)

intent_record = create_intent_record(
    gov,
    boundary,
    intent_receipt,
)

execution = _execute_verified_intent(intent_record)

state = {
    "status": "ACTIVE",
    "version": "1.0.0",
    "deployment": "SUCCESS",
}

state_receipt = create_state_receipt(
    execution,
    state,
)

state_record = create_state_record(
    state_receipt,
)

commit = commit_state(
    state_record,
    state_receipt,
    execution,
)

print(commit)
print(commit.to_dict())
