from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.boundary_receipt import create_boundary_receipt
from bvp.trust_root import (
    TrustedKeyRegistry,
    authenticate_boundary_receipt,
)
from decisionassure.human_approval import create_human_approval_evidence
from decisionassure.human_presence import create_human_presence_evidence
from decisionassure.human_approval_validation import validate_human_approval


now = datetime.now(timezone.utc).isoformat()

approval = create_human_approval_evidence(
    approver="human-approver-alice",
    decision_id="decision-two-source-001",
    intended_action="DEPLOY",
    governed_resource="production-service-A",
    policy_version="policy-v1",
    policy_reference="policy-ref-human-approval-001",
    approval_reference="human-approval-two-source-001",
    approval_status="APPROVED",
    approved_at=now,
    human_presence_claimed=True,
)

presence = create_human_presence_evidence(
    approval_evidence_hash=approval.evidence_hash,
    approver=approval.approver,
    decision_id=approval.decision_id,
    intended_action=approval.intended_action,
    governed_resource=approval.governed_resource,
    presence_reference="presence-two-source-001",
    observed_at=now,
    human_present=True,
)

registry = TrustedKeyRegistry()

human_key = Ed25519PrivateKey.generate()
presence_attestor_key = Ed25519PrivateKey.generate()

registry.register(
    "human-approver-alice",
    human_key.public_key(),
)

registry.register(
    "human-presence-attestor-001",
    presence_attestor_key.public_key(),
)

approval_receipt = create_boundary_receipt(
    sender="human-approver-alice",
    receiver="Veridian",
    artifact_type="HUMAN_APPROVAL",
    artifact=approval.to_dict(),
    policy_version="policy-v1",
)

approval_receipt = authenticate_boundary_receipt(
    approval_receipt,
    human_key,
)

presence_receipt = create_boundary_receipt(
    sender="human-presence-attestor-001",
    receiver="Veridian",
    artifact_type="HUMAN_PRESENCE",
    artifact=presence.to_dict(),
    policy_version="policy-v1",
)

presence_receipt = authenticate_boundary_receipt(
    presence_receipt,
    presence_attestor_key,
)

valid_result = validate_human_approval(
    approval,
    approval_receipt,
    presence,
    presence_receipt,
    registry,
)

print("TWO-SOURCE HUMAN APPROVAL:", valid_result)

assert valid_result.passed is True
assert valid_result.reason == "HUMAN_APPROVAL_VALIDATED"


# Adversarial case:
# The same trusted human signing path tries to manufacture both approval
# and the supposedly independent presence attestation.
agent_triggered_presence_receipt = create_boundary_receipt(
    sender="human-approver-alice",
    receiver="Veridian",
    artifact_type="HUMAN_PRESENCE",
    artifact=presence.to_dict(),
    policy_version="policy-v1",
)

agent_triggered_presence_receipt = authenticate_boundary_receipt(
    agent_triggered_presence_receipt,
    human_key,
)

denied_result = validate_human_approval(
    approval,
    approval_receipt,
    presence,
    agent_triggered_presence_receipt,
    registry,
)

print("NON-INDEPENDENT HUMAN APPROVAL:", denied_result)

assert denied_result.passed is False
assert denied_result.reason == "HUMAN_PRESENCE_NOT_INDEPENDENT"

print(
    "PASS: trusted approval signature alone could not manufacture "
    "independent human-presence provenance"
)
