from dataclasses import dataclass

from bvp.trust_root import verify_boundary_receipt_authenticity
from decisionassure.human_approval import verify_human_approval_evidence
from decisionassure.human_presence import verify_human_presence_evidence


@dataclass(frozen=True)
class HumanApprovalValidationResult:
    passed: bool
    reason: str


def validate_human_approval(
    approval_evidence,
    approval_boundary_receipt,
    presence_evidence,
    presence_boundary_receipt,
    trusted_key_registry,
) -> HumanApprovalValidationResult:
    if not verify_human_approval_evidence(approval_evidence):
        return HumanApprovalValidationResult(
            False,
            "INVALID_HUMAN_APPROVAL_EVIDENCE",
        )

    if not verify_human_presence_evidence(presence_evidence):
        return HumanApprovalValidationResult(
            False,
            "INVALID_HUMAN_PRESENCE_EVIDENCE",
        )

    if approval_boundary_receipt.artifact_type != "HUMAN_APPROVAL":
        return HumanApprovalValidationResult(
            False,
            "INVALID_HUMAN_APPROVAL_BOUNDARY",
        )

    if presence_boundary_receipt.artifact_type != "HUMAN_PRESENCE":
        return HumanApprovalValidationResult(
            False,
            "INVALID_HUMAN_PRESENCE_BOUNDARY",
        )

    if not verify_boundary_receipt_authenticity(
        approval_boundary_receipt,
        trusted_key_registry,
    ):
        return HumanApprovalValidationResult(
            False,
            "UNTRUSTED_HUMAN_APPROVAL_PROVENANCE",
        )

    if not verify_boundary_receipt_authenticity(
        presence_boundary_receipt,
        trusted_key_registry,
    ):
        return HumanApprovalValidationResult(
            False,
            "UNTRUSTED_HUMAN_PRESENCE_PROVENANCE",
        )

    # Presence must independently attest the exact approval evidence.
    if (
        presence_evidence.approval_evidence_hash
        != approval_evidence.evidence_hash
    ):
        return HumanApprovalValidationResult(
            False,
            "HUMAN_PRESENCE_APPROVAL_MISMATCH",
        )

    # Both artifacts must describe the same consequential event.
    bindings = (
        ("approver", approval_evidence.approver, presence_evidence.approver),
        (
            "decision_id",
            approval_evidence.decision_id,
            presence_evidence.decision_id,
        ),
        (
            "intended_action",
            approval_evidence.intended_action,
            presence_evidence.intended_action,
        ),
        (
            "governed_resource",
            approval_evidence.governed_resource,
            presence_evidence.governed_resource,
        ),
    )

    for field, approval_value, presence_value in bindings:
        if approval_value != presence_value:
            return HumanApprovalValidationResult(
                False,
                f"HUMAN_APPROVAL_BINDING_MISMATCH:{field}",
            )

    if approval_evidence.approval_status != "APPROVED":
        return HumanApprovalValidationResult(
            False,
            "HUMAN_APPROVAL_NOT_APPROVED",
        )

    if presence_evidence.human_present is not True:
        return HumanApprovalValidationResult(
            False,
            "HUMAN_PRESENCE_NOT_ATTESTED",
        )

    # Independence requirement:
    # the source asserting approval must not also be the source asserting
    # independent human presence.
    if (
        approval_boundary_receipt.sender
        == presence_boundary_receipt.sender
    ):
        return HumanApprovalValidationResult(
            False,
            "HUMAN_PRESENCE_NOT_INDEPENDENT",
        )

    return HumanApprovalValidationResult(
        True,
        "HUMAN_APPROVAL_VALIDATED",
    )
