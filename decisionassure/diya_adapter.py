from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from decisionassure.authority_scope import is_action_authorized
from decisionassure.responsibility_chain_validation import validate_responsibility_chain


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
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence=None,
    authority_state_boundary_receipt=None,
    execution_time=None,
):
    chain_validation = validate_responsibility_chain(
        responsibility_chain,
        decision,
        authority_evidence,
        authority_boundary_receipt,
        execution_time=execution_time,
        authority_state_evidence=authority_state_evidence,
        authority_state_boundary_receipt=authority_state_boundary_receipt,
    )

    if not chain_validation.passed:
        return DiyaVerificationResult(
            verification_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            decision_id=decision.decision_id,
            status="FAILED",
            reason=chain_validation.failed_condition or "UNAUTHORIZED_DELEGATION",
            intent_receipt_id=None,
        )

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
