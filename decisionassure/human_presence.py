from dataclasses import dataclass, asdict
from datetime import datetime
from hashlib import sha256
import json


@dataclass(frozen=True)
class HumanPresenceEvidence:
    """
    Evidence describing an independently attested human-presence event
    associated with a specific human approval.

    Supports deterministic integrity checking and exact binding to the
    approval evidence it attests.

    Does not by itself establish that the attesting source is trustworthy.
    That requires authenticated BoundaryReceipt provenance and trust-root
    validation.
    """

    evidence_hash: str
    approval_evidence_hash: str
    approver: str
    decision_id: str
    intended_action: str
    governed_resource: str
    presence_reference: str
    observed_at: str
    human_present: bool

    def to_dict(self):
        return asdict(self)


def create_human_presence_evidence(
    approval_evidence_hash: str,
    approver: str,
    decision_id: str,
    intended_action: str,
    governed_resource: str,
    presence_reference: str,
    observed_at: str,
    human_present: bool,
) -> HumanPresenceEvidence:
    required_strings = {
        "approval_evidence_hash": approval_evidence_hash,
        "approver": approver,
        "decision_id": decision_id,
        "intended_action": intended_action,
        "governed_resource": governed_resource,
        "presence_reference": presence_reference,
    }

    for name, value in required_strings.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    try:
        parsed_observed_at = datetime.fromisoformat(
            observed_at.replace("Z", "+00:00")
        )
    except (AttributeError, ValueError):
        raise ValueError("observed_at must be a valid ISO-8601 timestamp")

    if (
        parsed_observed_at.tzinfo is None
        or parsed_observed_at.utcoffset() is None
    ):
        raise ValueError("observed_at must be timezone-aware")

    if not isinstance(human_present, bool):
        raise ValueError("human_present must be boolean")

    payload = {
        "approval_evidence_hash": approval_evidence_hash,
        "approver": approver,
        "decision_id": decision_id,
        "intended_action": intended_action,
        "governed_resource": governed_resource,
        "presence_reference": presence_reference,
        "observed_at": observed_at,
        "human_present": human_present,
    }

    evidence_hash = sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return HumanPresenceEvidence(
        evidence_hash=evidence_hash,
        approval_evidence_hash=approval_evidence_hash,
        approver=approver,
        decision_id=decision_id,
        intended_action=intended_action,
        governed_resource=governed_resource,
        presence_reference=presence_reference,
        observed_at=observed_at,
        human_present=human_present,
    )


def verify_human_presence_evidence(
    evidence: HumanPresenceEvidence,
) -> bool:
    payload = {
        "approval_evidence_hash": evidence.approval_evidence_hash,
        "approver": evidence.approver,
        "decision_id": evidence.decision_id,
        "intended_action": evidence.intended_action,
        "governed_resource": evidence.governed_resource,
        "presence_reference": evidence.presence_reference,
        "observed_at": evidence.observed_at,
        "human_present": evidence.human_present,
    }

    recomputed_hash = sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return recomputed_hash == evidence.evidence_hash
