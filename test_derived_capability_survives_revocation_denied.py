from datetime import datetime, timezone

from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.decision_object import create_decision_object
from decisionassure.decision_replay import replay_denied_decision
from decisionassure.diya_adapter import verify_intent
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from executor.executor import _execute_verified_intent


# Adversarial class:
# DERIVED_CAPABILITY_SURVIVES_CONFIGURATION_ROLLBACK
#
# Second proof:
# authority was valid when a derived credential existed,
# authority is later revoked,
# the credential still physically exists,
# but it must not preserve permission for a protected action.

(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    decision_authority="Operations Committee",
    authority_scope="Production Deployment",
    agent="Deployment Agent",
    policy_reference="policy-ref-derived-revocation-001",
    evidence_reference="authority-evidence-derived-revocation-001",
    governed_resource="service-A",
)

active_time = "2026-10-01T09:00:00+00:00"
revocation_time = "2026-10-01T10:00:00+00:00"

initial_execution_time = datetime(
    2026, 10, 1, 9, 30, 0,
    tzinfo=timezone.utc,
)

post_revocation_execution_time = datetime(
    2026, 10, 1, 10, 5, 0,
    tzinfo=timezone.utc,
)


# ------------------------------------------------------------
# CASE 1
# Authority is active. A protected action is authorized.
# A derived credential is then treated as already issued.
# ------------------------------------------------------------

(
    active_state_evidence,
    active_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    effective_at=active_time,
    state_reference="derived-capability-active-001",
)

initial_decision = create_decision_object(
    requestor="deployment-agent-001",
    authority="Operations Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Deploy service while delegated authority is active",
    evidence_references=["deployment-evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "DEPLOYED"},
    governed_resource="service-A",
)

initial_gov = create_governance_receipt(initial_decision)

initial_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=initial_decision.to_dict(),
    policy_version="policy-v1",
)

initial_verification = verify_intent(
    initial_decision,
    initial_gov,
    initial_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    active_state_evidence,
    active_state_boundary_receipt,
    execution_time=initial_execution_time,
    trusted_key_registry=trusted_key_registry,
)

initial_intent_receipt = create_intent_receipt(
    initial_boundary,
    initial_verification,
)

initial_intent_record = create_intent_record(
    initial_gov,
    initial_boundary,
    initial_intent_receipt,
)

initial_execution = _execute_verified_intent(initial_intent_record)

print("PRE-REVOCATION VERIFICATION:", initial_verification.to_dict())
print("PRE-REVOCATION EXECUTION:", initial_execution.to_dict())

assert initial_verification.status == "VERIFIED"
assert initial_verification.verified_action == "DEPLOY"
assert initial_execution.status == "EXECUTED"
assert initial_execution.action == "DEPLOY"


# External derived capability already exists.
# It is deliberately NOT treated as authority by Veridian.
derived_credential = {
    "credential_id": "deployment-token-001",
    "resource": "service-A",
    "issued_while_authority_active": True,
}

assert derived_credential["issued_while_authority_active"] is True

print("DERIVED CREDENTIAL: PRESENT")


# ------------------------------------------------------------
# CASE 2
# Delegated authority is revoked.
# The already-issued credential still physically exists.
# ------------------------------------------------------------

(
    revoked_state_evidence,
    revoked_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="REVOKED",
    effective_at=revocation_time,
    state_reference="derived-capability-revoked-001",
)

post_revocation_decision = create_decision_object(
    requestor="deployment-agent-001",
    authority="Operations Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Use previously issued deployment credential after revocation",
    evidence_references=[
        "deployment-evidence-001",
        derived_credential["credential_id"],
    ],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "DEPLOYED"},
    governed_resource="service-A",
)

post_revocation_gov = create_governance_receipt(
    post_revocation_decision
)

post_revocation_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=post_revocation_decision.to_dict(),
    policy_version="policy-v1",
)

post_revocation_verification = verify_intent(
    post_revocation_decision,
    post_revocation_gov,
    post_revocation_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    revoked_state_evidence,
    revoked_state_boundary_receipt,
    execution_time=post_revocation_execution_time,
    trusted_key_registry=trusted_key_registry,
)

post_revocation_intent_receipt = create_intent_receipt(
    post_revocation_boundary,
    post_revocation_verification,
)

post_revocation_intent_record = create_intent_record(
    post_revocation_gov,
    post_revocation_boundary,
    post_revocation_intent_receipt,
)

post_revocation_execution = _execute_verified_intent(
    post_revocation_intent_record
)

print(
    "POST-REVOCATION VERIFICATION:",
    post_revocation_verification.to_dict(),
)
print(
    "POST-REVOCATION EXECUTION:",
    post_revocation_execution.to_dict(),
)

assert derived_credential is not None

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

print("DERIVED CREDENTIAL STILL PRESENT")
print("NO PROTECTED ACTION AFTER REVOCATION")


# ------------------------------------------------------------
# CASE 3
# Independently reproduce the denial from preserved evidence.
# ------------------------------------------------------------

replay_result = replay_denied_decision(
    decision=post_revocation_decision,
    governance_receipt=post_revocation_gov,
    responsibility_chain=responsibility_chain,
    boundary_receipt=post_revocation_boundary,
    boundary_artifact=post_revocation_decision.to_dict(),
    authority_evidence=authority_evidence,
    authority_boundary_receipt=authority_boundary_receipt,
    authority_state_evidence=revoked_state_evidence,
    authority_state_boundary_receipt=revoked_state_boundary_receipt,
    execution_time=post_revocation_execution_time,
    expected_failed_condition="REVOKED_AUTHORITY",
    trusted_key_registry=trusted_key_registry,
)

print("DERIVED CREDENTIAL REVOCATION REPLAY:", replay_result.to_dict())

assert replay_result.passed is True
assert (
    replay_result.message
    == "Authority denial independently reproduced: REVOKED_AUTHORITY"
)

print(
    "PASS: possession of an already-issued derived credential "
    "did not preserve authority after revocation"
)
