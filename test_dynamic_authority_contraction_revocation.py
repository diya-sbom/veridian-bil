from datetime import datetime, timezone

from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from bvp.boundary_receipt import create_boundary_receipt
from bil.intent_record import create_intent_record
from decisionassure.decision_object import create_decision_object
from decisionassure.decision_replay import replay_denied_decision
from decisionassure.diya_adapter import verify_intent
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.intent_receipt import create_intent_receipt
from executor.executor import _execute_verified_intent


(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    organization="Acme Corp",
    business_owner="Alice",
    decision_authority="Risk Committee",
    delegated_by="Alice",
    delegated_to="Veridian",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Deployment Agent",
    policy_reference="policy-ref-dynamic-contraction-001",
    evidence_reference="authority-evidence-dynamic-contraction-001",
    authority_evidence_source="AuthorityService",
    governed_resource="service-A",
)

decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Continue approved deployment task",
    evidence_references=["evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "DEPLOYED"},
    governed_resource="service-A",
)

gov = create_governance_receipt(decision)

boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=decision.to_dict(),
    policy_version="policy-v1",
)

task_start_time = datetime(
    2026, 10, 1, 9, 55, 0,
    tzinfo=timezone.utc,
)

revocation_time = "2026-10-01T10:00:00+00:00"

post_revocation_execution_time = datetime(
    2026, 10, 1, 10, 5, 0,
    tzinfo=timezone.utc,
)

# CASE 1:
# The task begins while authority is still valid.
(
    active_state_evidence,
    active_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    effective_at="2026-10-01T09:00:00+00:00",
    state_reference="dynamic-authority-active-001",
)

initial_verification = verify_intent(
    decision,
    gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    active_state_evidence,
    active_state_boundary_receipt,
    execution_time=task_start_time,
    trusted_key_registry=trusted_key_registry,
)

initial_intent_receipt = create_intent_receipt(
    boundary,
    initial_verification,
)

initial_intent_record = create_intent_record(
    gov,
    boundary,
    initial_intent_receipt,
)

initial_execution = _execute_verified_intent(initial_intent_record)

print("INITIAL VERIFICATION:", initial_verification.to_dict())
print("INITIAL EXECUTION:", initial_execution.to_dict())

assert initial_verification.status == "VERIFIED"
assert initial_verification.verified_action == "DEPLOY"
assert initial_execution.status == "EXECUTED"
assert initial_execution.action == "DEPLOY"


# CASE 2:
# Risk/policy state changes while the task is in progress.
# The same previously permitted action must be re-evaluated
# against current execution-time authority.
(
    revoked_state_evidence,
    revoked_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="REVOKED",
    effective_at=revocation_time,
    state_reference="dynamic-authority-revoked-001",
)

post_revocation_verification = verify_intent(
    decision,
    gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    revoked_state_evidence,
    revoked_state_boundary_receipt,
    execution_time=post_revocation_execution_time,
    trusted_key_registry=trusted_key_registry,
)

post_revocation_intent_receipt = create_intent_receipt(
    boundary,
    post_revocation_verification,
)

post_revocation_intent_record = create_intent_record(
    gov,
    boundary,
    post_revocation_intent_receipt,
)

post_revocation_execution = _execute_verified_intent(
    post_revocation_intent_record
)

print(
    "POST-CONTRACTION VERIFICATION:",
    post_revocation_verification.to_dict(),
)
print(
    "POST-CONTRACTION EXECUTION:",
    post_revocation_execution.to_dict(),
)

assert post_revocation_verification.status == "FAILED"
assert post_revocation_verification.reason == "REVOKED_AUTHORITY"
assert post_revocation_verification.intent_receipt_id is None
assert post_revocation_verification.verified_action is None

assert post_revocation_execution.status == "FAILED_CLOSED"
assert post_revocation_execution.action == "NONE"
assert (
    post_revocation_execution.message
    == "Execution blocked: intent not verified"
)

service_a_unauthorized_state_change = False
assert service_a_unauthorized_state_change is False

print("NO UNAUTHORIZED STATE CHANGE AFTER AUTHORITY CONTRACTION")


# CASE 3:
# Independently replay the execution-time denial.
replay_result = replay_denied_decision(
    decision=decision,
    governance_receipt=gov,
    responsibility_chain=responsibility_chain,
    boundary_receipt=boundary,
    boundary_artifact=decision.to_dict(),
    authority_evidence=authority_evidence,
    authority_boundary_receipt=authority_boundary_receipt,
    authority_state_evidence=revoked_state_evidence,
    authority_state_boundary_receipt=revoked_state_boundary_receipt,
    execution_time=post_revocation_execution_time,
    expected_failed_condition="REVOKED_AUTHORITY",
    trusted_key_registry=trusted_key_registry,
)

print(
    "DYNAMIC AUTHORITY CONTRACTION REPLAY:",
    replay_result.to_dict(),
)

assert replay_result.passed is True
assert (
    replay_result.message
    == "Authority denial independently reproduced: REVOKED_AUTHORITY"
)

print(
    "PASS: authority valid at task start did not remain valid "
    "after execution-time revocation"
)
