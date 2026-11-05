from datetime import datetime, timezone
from uuid import uuid4

from decisionassure.diya_adapter import (
    DiyaVerificationResult,
    verify_intent,
)
from decisionassure.human_approval_policy import (
    requires_independent_human_approval,
)
from decisionassure.human_approval_validation import validate_human_approval
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from executor.executor import _execute_verified_intent


def execute_with_current_authority(
    decision,
    governance_receipt,
    boundary_receipt,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time,
    trusted_key_registry,
    parent_authority_evidence=None,
    parent_authority_boundary_receipt=None,
    parent_authority_state_evidence=None,
    parent_authority_state_boundary_receipt=None,
    component_intent_receipts=None,
    human_approval_evidence=None,
    human_approval_boundary_receipt=None,
    human_presence_evidence=None,
    human_presence_boundary_receipt=None,
):
    """
    Revalidate authority immediately before execution.

    A previously VERIFIED record is not sufficient by itself.
    Current authority must still permit the action at execution time.

    For action/resource pairs protected by independent-human-approval
    policy, current authority is necessary but not sufficient:
    independently validated human approval provenance must also exist.
    """

    verification = verify_intent(
        decision,
        governance_receipt,
        boundary_receipt,
        responsibility_chain,
        authority_evidence,
        authority_boundary_receipt,
        authority_state_evidence=authority_state_evidence,
        authority_state_boundary_receipt=authority_state_boundary_receipt,
        execution_time=execution_time,
        parent_authority_evidence=parent_authority_evidence,
        parent_authority_boundary_receipt=parent_authority_boundary_receipt,
        parent_authority_state_evidence=parent_authority_state_evidence,
        parent_authority_state_boundary_receipt=parent_authority_state_boundary_receipt,
        component_intent_receipts=component_intent_receipts,
        trusted_key_registry=trusted_key_registry,
    )

    # Authority failure remains authoritative. Human approval must never
    # repair, replace, or expand missing authority.
    if (
        verification.status == "VERIFIED"
        and requires_independent_human_approval(
            decision.intended_action,
            decision.governed_resource,
        )
    ):
        approval_inputs = (
            human_approval_evidence,
            human_approval_boundary_receipt,
            human_presence_evidence,
            human_presence_boundary_receipt,
        )

        if any(value is None for value in approval_inputs):
            verification = DiyaVerificationResult(
                verification_id=str(uuid4()),
                timestamp=(
                    execution_time.isoformat()
                    if execution_time is not None
                    else datetime.now(timezone.utc).isoformat()
                ),
                decision_id=decision.decision_id,
                status="FAILED",
                reason="HUMAN_APPROVAL_REQUIRED",
                intent_receipt_id=None,
                verified_action=None,
            )
        else:
            approval_result = validate_human_approval(
                human_approval_evidence,
                human_approval_boundary_receipt,
                human_presence_evidence,
                human_presence_boundary_receipt,
                trusted_key_registry,
            )

            # Approval must bind to the exact consequential decision being
            # executed; a valid approval for another decision/action/resource
            # must never be reusable.
            decision_binding_valid = (
                human_approval_evidence.decision_id == decision.decision_id
                and human_approval_evidence.intended_action
                == decision.intended_action
                and human_approval_evidence.governed_resource
                == decision.governed_resource
                and human_approval_evidence.policy_version
                == decision.policy_version
            )

            if not approval_result.passed or not decision_binding_valid:
                reason = (
                    approval_result.reason
                    if not approval_result.passed
                    else "HUMAN_APPROVAL_DECISION_MISMATCH"
                )

                verification = DiyaVerificationResult(
                    verification_id=str(uuid4()),
                    timestamp=(
                        execution_time.isoformat()
                        if execution_time is not None
                        else datetime.now(timezone.utc).isoformat()
                    ),
                    decision_id=decision.decision_id,
                    status="FAILED",
                    reason=reason,
                    intent_receipt_id=None,
                    verified_action=None,
                )

    fresh_intent_receipt = create_intent_receipt(
        boundary_receipt,
        verification,
    )

    fresh_intent_record = create_intent_record(
        governance_receipt,
        boundary_receipt,
        fresh_intent_receipt,
    )

    execution = _execute_verified_intent(fresh_intent_record)

    return (
        verification,
        fresh_intent_receipt,
        fresh_intent_record,
        execution,
    )
