from dataclasses import dataclass
from typing import Any, Dict, Optional

from bvp.boundary_receipt import BoundaryReceipt
from bvp.verify_boundary import verify_boundary_receipt
from decisionassure.decision_object import DecisionObject
from decisionassure.governance_receipt import (
    GovernanceReceipt,
    create_governance_receipt,
)
from decisionassure.responsibility_chain import ResponsibilityChain


@dataclass(frozen=True)
class DecisionReplayResult:
    passed: bool
    message: str
    failed_stage: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "message": self.message,
            "failed_stage": self.failed_stage,
        }


def replay_decision(
    decision: DecisionObject,
    governance_receipt: GovernanceReceipt,
    responsibility_chain: ResponsibilityChain,
    boundary_receipt: BoundaryReceipt,
    boundary_artifact: Dict[str, Any],
) -> DecisionReplayResult:
    """
    Reconstruct and verify a governance decision using preserved evidence.

    Replay checks:
    - Governance Receipt integrity
    - Decision and receipt identity
    - Policy-version continuity
    - Authority continuity
    - Responsibility and delegation continuity
    - DecisionAssure-to-Diya boundary integrity
    """

    recomputed_receipt = create_governance_receipt(decision)

    if governance_receipt.receipt_hash != recomputed_receipt.receipt_hash:
        return DecisionReplayResult(
            passed=False,
            message="Governance Receipt hash mismatch",
            failed_stage="governance_receipt",
        )

    if governance_receipt.decision_id != decision.decision_id:
        return DecisionReplayResult(
            passed=False,
            message="Decision ID mismatch",
            failed_stage="decision_identity",
        )

    if governance_receipt.decision != decision.decision:
        return DecisionReplayResult(
            passed=False,
            message="Recorded governance decision mismatch",
            failed_stage="governance_decision",
        )

    if governance_receipt.policy_version != decision.policy_version:
        return DecisionReplayResult(
            passed=False,
            message="Decision and receipt policy versions do not match",
            failed_stage="policy_continuity",
        )

    if responsibility_chain.policy_version != decision.policy_version:
        return DecisionReplayResult(
            passed=False,
            message="Responsibility Chain policy version mismatch",
            failed_stage="responsibility_chain",
        )

    if responsibility_chain.decision_authority != decision.authority:
        return DecisionReplayResult(
            passed=False,
            message="Decision authority mismatch",
            failed_stage="authority_continuity",
        )

    if responsibility_chain.business_owner != decision.responsible_party:
        return DecisionReplayResult(
            passed=False,
            message="Responsible party mismatch",
            failed_stage="responsibility_continuity",
        )

    if responsibility_chain.delegated_to != "Veridian":
        return DecisionReplayResult(
            passed=False,
            message="Authority was not delegated to Veridian",
            failed_stage="delegation",
        )

    boundary_result = verify_boundary_receipt(
        receipt=boundary_receipt,
        artifact=boundary_artifact,
        expected_sender="DecisionAssure",
        expected_receiver="Diya",
    )

    if not boundary_result.passed:
        return DecisionReplayResult(
            passed=False,
            message=boundary_result.message,
            failed_stage="boundary_verification",
        )

    if boundary_receipt.policy_version != decision.policy_version:
        return DecisionReplayResult(
            passed=False,
            message="Boundary Receipt policy version mismatch",
            failed_stage="boundary_policy",
        )

    return DecisionReplayResult(
        passed=True,
        message="Decision replay verified",
    )


def replay_denied_decision(
    decision,
    governance_receipt,
    responsibility_chain,
    boundary_receipt,
    boundary_artifact,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time,
    expected_failed_condition,
    component_intent_receipts=None,
    trusted_key_registry=None,
) -> DecisionReplayResult:
    """
    Independently replay a pre-execution authority denial.

    The recorded denial is not treated as authority or proof.
    Replay first verifies the preserved governance/boundary evidence,
    then recomputes the execution-time authority result through the
    canonical Responsibility Chain validator.
    """

    base_replay = replay_decision(
        decision,
        governance_receipt,
        responsibility_chain,
        boundary_receipt,
        boundary_artifact,
    )

    if not base_replay.passed:
        return base_replay

    from decisionassure.responsibility_chain_validation import (
        validate_responsibility_chain,
    )

    authority_result = validate_responsibility_chain(
        responsibility_chain,
        decision,
        authority_evidence,
        authority_boundary_receipt,
        execution_time=execution_time,
        authority_state_evidence=authority_state_evidence,
        authority_state_boundary_receipt=authority_state_boundary_receipt,
        component_intent_receipts=component_intent_receipts,
        trusted_key_registry=trusted_key_registry,
    )

    if authority_result.passed:
        return DecisionReplayResult(
            passed=False,
            message="Replay expected authority denial but authority validated",
            failed_stage="authority_denial_replay",
        )

    if authority_result.failed_condition != expected_failed_condition:
        return DecisionReplayResult(
            passed=False,
            message=(
                "Recomputed authority denial does not match "
                "the expected failed condition"
            ),
            failed_stage="authority_denial_replay",
        )

    return DecisionReplayResult(
        passed=True,
        message=(
            "Authority denial independently reproduced: "
            f"{authority_result.failed_condition}"
        ),
    )
