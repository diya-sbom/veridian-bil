from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from decisionassure.approval_decision_binding import decision_binding_digest
from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.human_approval import create_human_approval_evidence
from decisionassure.human_presence import create_human_presence_evidence

from bvp.boundary_receipt import create_boundary_receipt
from bvp.trust_root import authenticate_boundary_receipt

from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture

from executor.guarded_execution import execute_with_current_authority


# ------------------------------------------------------------------
# Trusted deployment authority over the exact protected resource.
# ------------------------------------------------------------------

(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    decision_authority="Change Authority",
    authority_scope="Production Deployment",
    agent="Deployment Agent",
    policy_reference="policy-ref-deployment-001",
    evidence_reference="signed-deployment-mandate-001",
    governed_resource="production-service-A",
)

(
    active_state,
    active_state_boundary,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    effective_at="2026-11-04T20:00:00+00:00",
    state_reference="deployment-active-state-001",
)

execution_time = datetime(
    2026,
    11,
    4,
    22,
    0,
    tzinfo=timezone.utc,
)

deployment = create_decision_object(
    requestor="trusted-deployment-agent-001",
    authority="Change Authority",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Deploy authorized production change",
    evidence_references=["signed-deployment-mandate-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "DEPLOYED"},
    governed_resource="production-service-A",
)

gov = create_governance_receipt(deployment)

boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=deployment.to_dict(),
    policy_version="policy-v1",
)


# ------------------------------------------------------------------
# CASE 1:
# Authority is valid, but protected execution has no independent
# human approval provenance.
# ------------------------------------------------------------------

(
    denied_verification,
    denied_receipt,
    denied_record,
    denied_execution,
) = execute_with_current_authority(
    deployment,
    gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    active_state,
    active_state_boundary,
    execution_time,
    trusted_key_registry,
)

print("NO-APPROVAL VERIFICATION:", denied_verification.to_dict())
print("NO-APPROVAL EXECUTION:", denied_execution.to_dict())

assert denied_verification.status == "FAILED"
assert denied_verification.reason == "HUMAN_APPROVAL_REQUIRED"
assert denied_verification.intent_receipt_id is None
assert denied_verification.verified_action is None

assert denied_record.status == "FAILED"
assert denied_record.verified_action is None

assert denied_execution.status == "FAILED_CLOSED"
assert denied_execution.action == "NONE"

print(
    "PASS: valid deployment authority alone did not satisfy "
    "independent human approval policy"
)


# ------------------------------------------------------------------
# CASE 2:
# Same authority, same action, same resource, now accompanied by
# independently authenticated human approval and presence evidence.
# ------------------------------------------------------------------

approved_at = execution_time.isoformat()

human_approval = create_human_approval_evidence(
    approver="human-approver-alice",
    decision_id=deployment.decision_id,
    intended_action=deployment.intended_action,
    governed_resource=deployment.governed_resource,
    policy_version=deployment.policy_version,
    policy_reference="policy-ref-human-approval-001",
    approval_reference="human-approval-runtime-001",
    approval_status="APPROVED",
    approved_at=approved_at,
    human_presence_claimed=True,
    decision_binding_digest=decision_binding_digest(deployment),
)

human_presence = create_human_presence_evidence(
    approval_evidence_hash=human_approval.evidence_hash,
    approver=human_approval.approver,
    decision_id=deployment.decision_id,
    intended_action=deployment.intended_action,
    governed_resource=deployment.governed_resource,
    presence_reference="presence-runtime-001",
    observed_at=approved_at,
    human_present=True,
)

human_key = Ed25519PrivateKey.generate()
presence_key = Ed25519PrivateKey.generate()

trusted_key_registry.register(
    "human-approver-alice",
    human_key.public_key(),
)

trusted_key_registry.register(
    "human-presence-attestor-001",
    presence_key.public_key(),
)

human_approval_boundary = create_boundary_receipt(
    sender="human-approver-alice",
    receiver="Veridian",
    artifact_type="HUMAN_APPROVAL",
    artifact=human_approval.to_dict(),
    policy_version="policy-v1",
)

human_approval_boundary = authenticate_boundary_receipt(
    human_approval_boundary,
    human_key,
)

human_presence_boundary = create_boundary_receipt(
    sender="human-presence-attestor-001",
    receiver="Veridian",
    artifact_type="HUMAN_PRESENCE",
    artifact=human_presence.to_dict(),
    policy_version="policy-v1",
)

human_presence_boundary = authenticate_boundary_receipt(
    human_presence_boundary,
    presence_key,
)

(
    approved_verification,
    approved_receipt,
    approved_record,
    approved_execution,
) = execute_with_current_authority(
    deployment,
    gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    active_state,
    active_state_boundary,
    execution_time,
    trusted_key_registry,
    human_approval_evidence=human_approval,
    human_approval_boundary_receipt=human_approval_boundary,
    human_presence_evidence=human_presence,
    human_presence_boundary_receipt=human_presence_boundary,
)

print("APPROVED VERIFICATION:", approved_verification.to_dict())
print("APPROVED EXECUTION:", approved_execution.to_dict())

assert approved_verification.status == "VERIFIED"
assert approved_verification.verified_action == "DEPLOY"

assert approved_record.status == "VERIFIED"
assert approved_record.verified_action == "DEPLOY"

assert approved_execution.status == "EXECUTED"
assert approved_execution.action == "DEPLOY"

print(
    "PASS: protected deployment executed only with current authority "
    "and independently validated human approval provenance"
)

# CASE 3: Reuse approval after materially changing deployment state.
# The original decision ID, action, resource and approval stay unchanged.
# This must fail closed before execution.
from dataclasses import replace

changed_deployment = replace(
    deployment,
    intended_state={"status": "UNAPPROVED_VERSION"},
)

(
    changed_verification,
    changed_receipt,
    changed_record,
    changed_execution,
) = execute_with_current_authority(
    changed_deployment,
    gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    active_state,
    active_state_boundary,
    execution_time,
    trusted_key_registry,
    human_approval_evidence=human_approval,
    human_approval_boundary_receipt=human_approval_boundary,
    human_presence_evidence=human_presence,
    human_presence_boundary_receipt=human_presence_boundary,
)

print("CHANGED-STATE VERIFICATION:", changed_verification.to_dict())
print("CHANGED-STATE EXECUTION:", changed_execution.to_dict())

assert changed_verification.status == "FAILED", (
    "SECURITY FAILURE: changed deployment was verified using stale approval"
)
assert changed_execution.status == "FAILED_CLOSED", (
    "SECURITY FAILURE: changed deployment was executed"
)
assert changed_execution.action == "NONE"

print("PASS: changed deployment state rejected before execution")
