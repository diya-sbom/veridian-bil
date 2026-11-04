from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.boundary_receipt import create_boundary_receipt
from bvp.trust_root import (
    TrustedKeyRegistry,
    authenticate_boundary_receipt,
    verify_boundary_receipt_authenticity,
)
from decisionassure.human_approval import (
    create_human_approval_evidence,
    verify_human_approval_evidence,
)


approved_at = datetime.now(timezone.utc).isoformat()

approval = create_human_approval_evidence(
    approver="human-approver-alice",
    decision_id="decision-approval-gap-001",
    intended_action="DEPLOY",
    governed_resource="production-service-A",
    policy_version="policy-v1",
    policy_reference="policy-ref-human-approval-001",
    approval_reference="agent-triggered-approval-001",
    approval_status="APPROVED",
    approved_at=approved_at,
    human_presence_claimed=True,
)

assert verify_human_approval_evidence(approval) is True

registry = TrustedKeyRegistry()
human_signing_key = Ed25519PrivateKey.generate()

registry.register(
    "human-approver-alice",
    human_signing_key.public_key(),
)

# Adversarial condition:
# the agent can invoke the same trusted signing path intended for the human.
agent_triggered_receipt = create_boundary_receipt(
    sender="human-approver-alice",
    receiver="Veridian",
    artifact_type="HUMAN_APPROVAL",
    artifact=approval.to_dict(),
    policy_version="policy-v1",
)

agent_triggered_receipt = authenticate_boundary_receipt(
    agent_triggered_receipt,
    human_signing_key,
)

accepted_as_authentic = verify_boundary_receipt_authenticity(
    agent_triggered_receipt,
    registry,
)

print(
    "AGENT-TRIGGERED TRUSTED HUMAN SIGNATURE ACCEPTED:",
    accepted_as_authentic,
)

assert accepted_as_authentic is True

print(
    "GAP CONFIRMED: trusted signature provenance alone cannot prove "
    "independent human presence when the agent can invoke the human signing path"
)
