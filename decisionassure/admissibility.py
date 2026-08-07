from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from decisionassure.decision_object import DecisionObject
from decisionassure.decision_replay import DecisionReplayResult


VALID_ADMISSIBILITY_RESULTS = {
    "ADMISSIBLE",
    "NOT_ADMISSIBLE",
    "REQUIRES_REVIEW",
}


@dataclass(frozen=True)
class AdmissibilityResult:
    admissibility_id: str
    timestamp: str
    decision_id: str
    result: str
    reason: str
    reviewer: str
    checks: Dict[str, bool]
    failed_check: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_admissibility(
    decision: DecisionObject,
    replay_result: DecisionReplayResult,
    reviewer: str,
    required_evidence: Optional[List[str]] = None,
) -> AdmissibilityResult:
    """
    Determine whether a governance decision has sufficient
    independently verifiable evidence to proceed.

    Admissibility does not execute the decision.
    It evaluates whether the preserved governance evidence
    is complete, consistent, and replayable.
    """

    if not reviewer.strip():
        raise ValueError("reviewer is required")

    required_evidence = required_evidence or []

    evidence_complete = all(
        reference in decision.evidence_references
        for reference in required_evidence
    )

    checks = {
        "replay_verified": replay_result.passed,
        "decision_approved": decision.decision == "APPROVED",
        "authority_present": bool(decision.authority.strip()),
        "policy_present": bool(decision.policy_version.strip()),
        "responsible_party_present": bool(
            decision.responsible_party.strip()
        ),
        "intent_present": bool(decision.intent.strip()),
        "evidence_present": bool(decision.evidence_references),
        "required_evidence_complete": evidence_complete,
    }

    failed_check = next(
        (name for name, passed in checks.items() if not passed),
        None,
    )

    if failed_check is not None:
        if (
            decision.decision == "REQUIRES_REVIEW"
            and failed_check == "decision_approved"
        ):
            result = "REQUIRES_REVIEW"
            reason = "Decision requires additional governance review"
        else:
            result = "NOT_ADMISSIBLE"
            reason = f"Admissibility check failed: {failed_check}"
    else:
        result = "ADMISSIBLE"
        reason = "Governance evidence is complete and replay verified"

    from uuid import uuid4

    return AdmissibilityResult(
        admissibility_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        decision_id=decision.decision_id,
        result=result,
        reason=reason,
        reviewer=reviewer,
        checks=checks,
        failed_check=failed_check,
    )
