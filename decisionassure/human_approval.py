from dataclasses import dataclass, asdict
from datetime import datetime
from hashlib import sha256
import json


VALID_APPROVAL_STATUSES = {
    "APPROVED",
    "DENIED",
}


@dataclass(frozen=True)
class HumanApprovalEvidence:
    """
    Evidence describing a claimed human approval event.

    Supports:
    - deterministic integrity checking;
    - exact binding to decision, action, resource, and policy;
    - recording the claimed human approver and approval event;
    - later binding to a cryptographically authenticated BoundaryReceipt.

    Does not by itself establish:
    - that the named approver is a human;
    - that the human was physically/presently involved;
    - that the approval channel was inaccessible to an agent;
    - that the approver had authority to approve the action.

    Those properties require trusted provenance and authority validation.
    """

    evidence_hash: str
    approver: str
    decision_id: str
    intended_action: str
    governed_resource: str
    policy_version: str
    policy_reference: str
    approval_reference: str
    approval_status: str
    approved_at: str
    human_presence_claimed: bool
    decision_binding_digest: str | None = None

    def to_dict(self):
        return asdict(self)


def create_human_approval_evidence(
    approver: str,
    decision_id: str,
    intended_action: str,
    governed_resource: str,
    policy_version: str,
    policy_reference: str,
    approval_reference: str,
    approval_status: str,
    approved_at: str,
    human_presence_claimed: bool,
    decision_binding_digest: str | None = None,
) -> HumanApprovalEvidence:
    if approval_status not in VALID_APPROVAL_STATUSES:
        raise ValueError(
            "approval_status must be one of "
            f"{sorted(VALID_APPROVAL_STATUSES)}"
        )

    required_strings = {
        "approver": approver,
        "decision_id": decision_id,
        "intended_action": intended_action,
        "governed_resource": governed_resource,
        "policy_version": policy_version,
        "policy_reference": policy_reference,
        "approval_reference": approval_reference,
    }

    for name, value in required_strings.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    try:
        parsed_approved_at = datetime.fromisoformat(
            approved_at.replace("Z", "+00:00")
        )
    except (AttributeError, ValueError):
        raise ValueError("approved_at must be a valid ISO-8601 timestamp")

    if (
        parsed_approved_at.tzinfo is None
        or parsed_approved_at.utcoffset() is None
    ):
        raise ValueError("approved_at must be timezone-aware")

    if not isinstance(human_presence_claimed, bool):
        raise ValueError("human_presence_claimed must be boolean")

    payload = {
        "approver": approver,
        "decision_id": decision_id,
        "intended_action": intended_action,
        "governed_resource": governed_resource,
        "policy_version": policy_version,
        "policy_reference": policy_reference,
        "approval_reference": approval_reference,
        "approval_status": approval_status,
        "approved_at": approved_at,
        "human_presence_claimed": human_presence_claimed,
    }

    if decision_binding_digest is not None:
        if (
            not isinstance(decision_binding_digest, str)
            or len(decision_binding_digest) != 64
            or any(c not in "0123456789abcdef" for c in decision_binding_digest)
        ):
            raise ValueError("Invalid decision binding digest")
        payload["decision_binding_digest"] = decision_binding_digest

    evidence_hash = sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return HumanApprovalEvidence(
        evidence_hash=evidence_hash,
        approver=approver,
        decision_id=decision_id,
        intended_action=intended_action,
        governed_resource=governed_resource,
        policy_version=policy_version,
        policy_reference=policy_reference,
        approval_reference=approval_reference,
        approval_status=approval_status,
        approved_at=approved_at,
        human_presence_claimed=human_presence_claimed,
        decision_binding_digest=decision_binding_digest,
    )


def verify_human_approval_evidence(
    evidence: HumanApprovalEvidence,
) -> bool:
    payload = {
        "approver": evidence.approver,
        "decision_id": evidence.decision_id,
        "intended_action": evidence.intended_action,
        "governed_resource": evidence.governed_resource,
        "policy_version": evidence.policy_version,
        "policy_reference": evidence.policy_reference,
        "approval_reference": evidence.approval_reference,
        "approval_status": evidence.approval_status,
        "approved_at": evidence.approved_at,
        "human_presence_claimed": evidence.human_presence_claimed,
    }

    if evidence.decision_binding_digest is not None:
        digest = evidence.decision_binding_digest
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
        ):
            return False
        payload["decision_binding_digest"] = digest

    recomputed_hash = sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return recomputed_hash == evidence.evidence_hash
