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
    decision_id="decision-approval-001",
    intended_action="DEPLOY",
    governed_resource="production-service-A",
    policy_version="policy-v1",
    policy_reference="policy-ref-human-approval-001",
    approval_reference="human-approval-001",
    approval_status="APPROVED",
    approved_at=approved_at,
    human_presence_claimed=True,
)

assert verify_human_approval_evidence(approval) is True

trusted_registry = TrustedKeyRegistry()
human_signing_key = Ed25519PrivateKey.generate()

trusted_registry.register(
    "human-approver-alice",
    human_signing_key.public_key(),
)

human_receipt = create_boundary_receipt(
    sender="human-approver-alice",
    receiver="Veridian",
    artifact_type="HUMAN_APPROVAL",
    artifact=approval.to_dict(),
    policy_version="policy-v1",
)

human_receipt = authenticate_boundary_receipt(
    human_receipt,
    human_signing_key,
)

assert human_receipt.artifact_type == "HUMAN_APPROVAL"
assert verify_boundary_receipt_authenticity(
    human_receipt,
    trusted_registry,
) is True

print("TRUSTED HUMAN APPROVAL PROVENANCE: VERIFIED")


# Agent possesses the approval data, but does not possess the trusted human key.
agent_signing_key = Ed25519PrivateKey.generate()

agent_receipt = create_boundary_receipt(
    sender="personal-ai-agent-001",
    receiver="Veridian",
    artifact_type="HUMAN_APPROVAL",
    artifact=approval.to_dict(),
    policy_version="policy-v1",
)

agent_receipt = authenticate_boundary_receipt(
    agent_receipt,
    agent_signing_key,
)

assert verify_boundary_receipt_authenticity(
    agent_receipt,
    trusted_registry,
) is False

print(
    "PASS: possession of human approval evidence did not let the agent "
    "manufacture trusted human approval provenance"
)
