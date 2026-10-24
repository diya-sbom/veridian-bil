from datetime import datetime, timezone

from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.decision_object import create_decision_object
from decisionassure.diya_adapter import verify_intent
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from executor.executor import _execute_verified_intent


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

revocation_time = "2026-10-01T10:00:00+00:00"
execution_time = datetime(
    2026, 10, 1, 10, 5, 0,
    tzinfo=timezone.utc,
)

(
    authority_state_evidence,
    authority_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="REVOKED",
    effective_at=revocation_time,
    state_reference="revocation-001",
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
    execution_time=execution_time,
    trusted_key_registry=trusted_key_registry,
)

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

print("VERIFICATION:", verification.to_dict())
print("EXECUTION:", execution.to_dict())

assert verification.status == "FAILED"
assert verification.reason == "REVOKED_AUTHORITY"
assert verification.intent_receipt_id is None

assert execution.status == "FAILED_CLOSED"
assert execution.action == "NONE"
assert execution.message == "Execution blocked: intent not verified"

print(
    "PASS: authority valid earlier, revoked before execution, "
    "no execution authority remained"
)
