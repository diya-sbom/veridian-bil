from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from bvp.boundary_receipt import BoundaryReceipt
from bvp.verify_boundary import verify_boundary_receipt
from decisionassure.authority_delegation import (
    AuthorityDelegationEvidence,
    verify_authority_delegation_evidence,
)
from decisionassure.authority_scope import is_action_authorized
from decisionassure.responsibility_chain import ResponsibilityChain


@dataclass(frozen=True)
class ResponsibilityChainValidationResult:
    passed: bool
    reason: str
    failed_condition: Optional[str] = None


def validate_responsibility_chain(
    responsibility_chain: ResponsibilityChain,
    decision,
    authority_evidence: AuthorityDelegationEvidence,
    authority_boundary_receipt: BoundaryReceipt,
    execution_time: Optional[datetime] = None,
) -> ResponsibilityChainValidationResult:
    """
    Deterministically validate Responsibility Chain semantics.

    Unknown or insufficient authority evidence fails closed.
    """

    if not responsibility_chain.decision_authority.strip():
        return ResponsibilityChainValidationResult(
            passed=False,
            reason="Originating decision authority is missing",
            failed_condition="UNKNOWN_AUTHORITY",
        )

    required_links = (
        responsibility_chain.organization,
        responsibility_chain.business_owner,
        responsibility_chain.delegated_by,
        responsibility_chain.delegated_to,
        responsibility_chain.ai_system,
        responsibility_chain.agent,
        responsibility_chain.policy_reference,
        responsibility_chain.evidence_reference,
    )

    if any(not value or not value.strip() for value in required_links):
        return ResponsibilityChainValidationResult(
            passed=False,
            reason="Required responsibility chain linkage is missing",
            failed_condition="BROKEN_CHAIN",
        )

    if responsibility_chain.policy_version != decision.policy_version:
        return ResponsibilityChainValidationResult(
            passed=False,
            reason="Responsibility Chain policy version mismatch",
            failed_condition="BROKEN_CHAIN",
        )

    if responsibility_chain.decision_authority != decision.authority:
        return ResponsibilityChainValidationResult(
            passed=False,
            reason="Decision authority mismatch",
            failed_condition="BROKEN_CHAIN",
        )

    if responsibility_chain.business_owner != decision.responsible_party:
        return ResponsibilityChainValidationResult(
            passed=False,
            reason="Responsible party mismatch",
            failed_condition="BROKEN_CHAIN",
        )

    if not verify_authority_delegation_evidence(authority_evidence):
        return ResponsibilityChainValidationResult(
            passed=False,
            reason="Authority delegation evidence integrity failed",
            failed_condition="UNAUTHORIZED_DELEGATION",
        )

    if not responsibility_chain.authority_evidence_source or not responsibility_chain.authority_evidence_source.strip():
        return ResponsibilityChainValidationResult(
            passed=False,
            reason="Authority evidence source is missing",
            failed_condition="BROKEN_CHAIN",
        )

    boundary_result = verify_boundary_receipt(
        receipt=authority_boundary_receipt,
        artifact=authority_evidence.to_dict(),
        expected_sender=responsibility_chain.authority_evidence_source,
        expected_receiver="Veridian",
        expected_artifact_type="AUTHORITY_DELEGATION",
        expected_policy_version=responsibility_chain.policy_version,
    )

    if not boundary_result.passed:
        return ResponsibilityChainValidationResult(
            passed=False,
            reason=f"Authority delegation boundary verification failed: {boundary_result.message}",
            failed_condition="UNAUTHORIZED_DELEGATION",
        )

    if (
        authority_evidence.delegator != responsibility_chain.delegated_by
        or authority_evidence.delegatee != responsibility_chain.delegated_to
        or authority_evidence.authority_scope != responsibility_chain.authority_scope
        or authority_evidence.policy_version != responsibility_chain.policy_version
        or authority_evidence.policy_reference != responsibility_chain.policy_reference
        or authority_evidence.evidence_reference != responsibility_chain.evidence_reference
    ):
        return ResponsibilityChainValidationResult(
            passed=False,
            reason="Authority delegation evidence does not match Responsibility Chain",
            failed_condition="UNAUTHORIZED_DELEGATION",
        )

    if authority_evidence.delegation_status != "AUTHORIZED":
        return ResponsibilityChainValidationResult(
            passed=False,
            reason="Delegation is not authorized",
            failed_condition="UNAUTHORIZED_DELEGATION",
        )

    if responsibility_chain.valid_until is not None:
        try:
            valid_until = datetime.fromisoformat(
                responsibility_chain.valid_until.replace("Z", "+00:00")
            )
        except ValueError:
            return ResponsibilityChainValidationResult(
                passed=False,
                reason="Authority validity timestamp is invalid",
                failed_condition="BROKEN_CHAIN",
            )

        if valid_until.tzinfo is None:
            return ResponsibilityChainValidationResult(
                passed=False,
                reason="Authority validity timestamp must be timezone-aware",
                failed_condition="BROKEN_CHAIN",
            )

        if execution_time is not None and (
            execution_time.tzinfo is None
            or execution_time.utcoffset() is None
        ):
            return ResponsibilityChainValidationResult(
                passed=False,
                reason="Execution time must be timezone-aware",
                failed_condition="BROKEN_CHAIN",
            )

        now = execution_time or datetime.now(timezone.utc)

        if now > valid_until:
            return ResponsibilityChainValidationResult(
                passed=False,
                reason="Authority grant has expired",
                failed_condition="EXPIRED_AUTHORITY",
            )

    if not is_action_authorized(
        responsibility_chain.authority_scope,
        decision.intended_action,
    ):
        return ResponsibilityChainValidationResult(
            passed=False,
            reason="Intended action is outside delegated authority scope",
            failed_condition="OUT_OF_SCOPE",
        )

    return ResponsibilityChainValidationResult(
        passed=True,
        reason="Responsibility Chain verified",
    )
