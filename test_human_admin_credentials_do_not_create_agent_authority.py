from datetime import datetime, timezone

from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.intent_receipt import verify_denial_receipt
from bvp.boundary_receipt import create_boundary_receipt
from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from executor.guarded_execution import execute_with_current_authority


# A human legitimately holds production administrative credentials.
# The personal AI agent can access those credentials.
# Credential access must NOT become delegated agent authority.
human_admin_credentials = {"PRODUCTION_ADMIN"}
agent_credential_access = True

protected_state = {
    "production_code_version": "v1",
    "production_modified": False,
}

decision = create_decision_object(
    requestor="personal-ai-agent-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Modify production code using accessible human admin credentials",
    evidence_references=["human-admin-credential-access-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"production_code": "MODIFIED"},
)

gov = create_governance_receipt(decision)

(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    authority_scope="Agreement Operations",
)

(
    authority_state_evidence,
    authority_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    state_reference="human-admin-credential-state-001",
)

boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=decision.to_dict(),
    policy_version="policy-v1",
)

assert "PRODUCTION_ADMIN" in human_admin_credentials
assert agent_credential_access is True
assert authority_evidence.authority_scope == "Agreement Operations"

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
    "production_code_version": "v1",
    "production_modified": False,
}

print(
    "PASS: human admin credential access did not create agent authority; "
    "production modification failed closed with no unauthorized state change"
)
print("PASS: denial evidence independently verifies")
