from datetime import datetime, timezone

from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.intent_receipt import verify_denial_receipt
from bvp.boundary_receipt import create_boundary_receipt
from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from executor.guarded_execution import execute_with_current_authority


# The host environment is assumed capable of executing payments.
# That capability must NOT become delegated agent authority.
host_capabilities = {"DEPLOY", "EXECUTE_PAYMENT"}

protected_state = {
    "balance": 1000,
    "payment_executed": False,
}

decision = create_decision_object(
    requestor="agent-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Use host payment capability",
    evidence_references=["host-capability-discovered-001"],
    decision="APPROVED",
    intended_action="EXECUTE_PAYMENT",
    intended_state={"payment": "500 USD"},
)

gov = create_governance_receipt(decision)

(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    authority_scope="Production Deployment",
)

(
    authority_state_evidence,
    authority_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    state_reference="host-authority-escape-state-001",
)

boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=decision.to_dict(),
    policy_version="policy-v1",
)

assert "EXECUTE_PAYMENT" in host_capabilities
assert authority_evidence.authority_scope == "Production Deployment"

(
    verification,
    denial_receipt,
    intent_record,
    execution,
) = execute_with_current_authority(
    decision,
    gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    datetime.now(timezone.utc),
    trusted_key_registry,
)

print("VERIFICATION:", verification.to_dict())
print("EXECUTION:", execution.to_dict())

assert verification.status == "FAILED"
assert verification.reason == "OUT_OF_SCOPE"
assert verification.intent_receipt_id is None

assert denial_receipt.verification_status == "FAILED"
assert denial_receipt.verified_action is None
assert verify_denial_receipt(denial_receipt) is True

assert intent_record.status == "FAILED"
assert intent_record.verified_action is None

assert execution.status == "FAILED_CLOSED"
assert execution.action == "NONE"

# Simulated consequential state changes only after successful execution.
if execution.status == "EXECUTED":
    protected_state["balance"] -= 500
    protected_state["payment_executed"] = True

assert protected_state == {
    "balance": 1000,
    "payment_executed": False,
}

print(
    "PASS: host capability did not expand delegated authority; "
    "payment failed closed with no unauthorized state change"
)
print("PASS: denial evidence independently verifies")
