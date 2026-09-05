from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from decisionassure.authority_scope import is_action_authorized


@dataclass
class DiyaVerificationResult:
    verification_id: str
    timestamp: str
    decision_id: str
    status: str
    reason: str
    intent_receipt_id: str

    def to_dict(self):
        return self.__dict__


def verify_intent(
    decision,
    governance_receipt,
    boundary_receipt,
    responsibility_chain,
):
    if decision.decision != "APPROVED":
        return DiyaVerificationResult(
            verification_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_id=decision.decision_id,
            status="FAILED",
            reason="Decision not approved",
            intent_receipt_id=None,
        )

    if not is_action_authorized(
        responsibility_chain.authority_scope,
        decision.intended_action,
    ):
        return DiyaVerificationResult(
            verification_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_id=decision.decision_id,
            status="FAILED",
            reason="OUT_OF_SCOPE",
            intent_receipt_id=None,
        )

    intent_receipt_id = str(uuid.uuid4())

    return DiyaVerificationResult(
        verification_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        decision_id=decision.decision_id,
        status="VERIFIED",
        reason="Intent verified",
        intent_receipt_id=intent_receipt_id,
    )
