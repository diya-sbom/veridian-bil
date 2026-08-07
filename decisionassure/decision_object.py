from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


VALID_DECISIONS = {
    "APPROVED",
    "DENIED",
    "REQUIRES_REVIEW",
}


@dataclass(frozen=True)
class DecisionObject:
    """
    Immutable record of a governance decision.

    The object preserves the authority, responsibility, policy,
    evidence, intent, and intended state associated with the decision.
    """

    decision_id: str
    timestamp: str
    requestor: str
    authority: str
    responsible_party: str
    policy_version: str
    intent: str
    evidence_references: List[str]
    decision: str
    intended_action: str
    intended_state: Dict[str, Any]

    def __post_init__(self) -> None:
        if not self.decision_id.strip():
            raise ValueError("decision_id is required")

        if not self.requestor.strip():
            raise ValueError("requestor is required")

        if not self.authority.strip():
            raise ValueError("authority is required")

        if not self.responsible_party.strip():
            raise ValueError("responsible_party is required")

        if not self.policy_version.strip():
            raise ValueError("policy_version is required")

        if not self.intent.strip():
            raise ValueError("intent is required")

        if not self.evidence_references:
            raise ValueError("At least one evidence reference is required")

        if self.decision not in VALID_DECISIONS:
            raise ValueError(
                f"decision must be one of: {sorted(VALID_DECISIONS)}"
            )

        if not self.intended_action.strip():
            raise ValueError("intended_action is required")

    def to_dict(self) -> Dict[str, Any]:
        """Return a serializable representation of the decision."""
        return asdict(self)


def create_decision_object(
    requestor: str,
    authority: str,
    responsible_party: str,
    policy_version: str,
    intent: str,
    evidence_references: List[str],
    decision: str,
    intended_action: str,
    intended_state: Dict[str, Any],
) -> DecisionObject:
    """Create a new immutable Decision Object."""

    return DecisionObject(
        decision_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        requestor=requestor,
        authority=authority,
        responsible_party=responsible_party,
        policy_version=policy_version,
        intent=intent,
        evidence_references=evidence_references,
        decision=decision,
        intended_action=intended_action,
        intended_state=intended_state,
    )
