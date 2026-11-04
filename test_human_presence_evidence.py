from dataclasses import replace
from datetime import datetime, timezone

from decisionassure.human_approval import create_human_approval_evidence
from decisionassure.human_presence import (
    create_human_presence_evidence,
    verify_human_presence_evidence,
)


now = datetime.now(timezone.utc).isoformat()

approval = create_human_approval_evidence(
    approver="human-approver-alice",
    decision_id="decision-presence-001",
    intended_action="DEPLOY",
    governed_resource="production-service-A",
    policy_version="policy-v1",
    policy_reference="policy-ref-human-approval-001",
    approval_reference="human-approval-presence-001",
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
    presence_reference="presence-attestation-001",
    observed_at=now,
    human_present=True,
)

print("HUMAN PRESENCE EVIDENCE:", presence.to_dict())

assert verify_human_presence_evidence(presence) is True
assert presence.approval_evidence_hash == approval.evidence_hash
assert presence.human_present is True

tampered_approval_link = replace(
    presence,
    approval_evidence_hash="wrong-approval-hash",
)
assert verify_human_presence_evidence(tampered_approval_link) is False

tampered_action = replace(
    presence,
    intended_action="EXECUTE_PAYMENT",
)
assert verify_human_presence_evidence(tampered_action) is False

tampered_presence = replace(
    presence,
    human_present=False,
)
assert verify_human_presence_evidence(tampered_presence) is False

print(
    "PASS: human presence evidence integrity binds approval, action, "
    "resource, and presence claim"
)
