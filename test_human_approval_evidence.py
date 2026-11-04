from dataclasses import replace
from datetime import datetime, timezone

from decisionassure.human_approval import (
    create_human_approval_evidence,
    verify_human_approval_evidence,
)


approved_at = datetime.now(timezone.utc).isoformat()

evidence = create_human_approval_evidence(
    approver="human-approver-alice",
    decision_id="decision-001",
    intended_action="DEPLOY",
    governed_resource="production-service-A",
    policy_version="policy-v1",
    policy_reference="policy-ref-human-approval-001",
    approval_reference="human-approval-001",
    approval_status="APPROVED",
    approved_at=approved_at,
    human_presence_claimed=True,
)

print("HUMAN APPROVAL EVIDENCE:", evidence.to_dict())

assert verify_human_approval_evidence(evidence) is True
assert evidence.approver == "human-approver-alice"
assert evidence.intended_action == "DEPLOY"
assert evidence.governed_resource == "production-service-A"
assert evidence.approval_status == "APPROVED"
assert evidence.human_presence_claimed is True

# Integrity test: modifying a bound consequential field must invalidate evidence.
tampered_action = replace(
    evidence,
    intended_action="EXECUTE_PAYMENT",
)

assert verify_human_approval_evidence(tampered_action) is False

# Integrity test: changing the claimed approval status must also invalidate evidence.
tampered_status = replace(
    evidence,
    approval_status="DENIED",
)

assert verify_human_approval_evidence(tampered_status) is False

print("PASS: human approval evidence integrity binds approver, action, resource, and approval claim")
