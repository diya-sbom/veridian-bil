from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, Optional

from bvp.boundary_receipt import BoundaryReceipt, canonical_json


@dataclass(frozen=True)
class BoundaryVerificationResult:
    passed: bool
    message: str
    failed_field: Optional[str] = None


def verify_boundary_receipt(
    receipt: BoundaryReceipt,
    artifact: Dict[str, Any],
    expected_sender: Optional[str] = None,
    expected_receiver: Optional[str] = None,
    expected_previous_receipt_hash: Optional[str] = None,
) -> BoundaryVerificationResult:
    """
    Independently verify a Boundary Receipt.

    Verification confirms:
    - artifact integrity
    - receipt integrity
    - sender identity
    - receiver identity
    - receipt-chain continuity
    - successful verification status
    """

    recomputed_artifact_hash = sha256(
        canonical_json(artifact).encode("utf-8")
    ).hexdigest()

    if recomputed_artifact_hash != receipt.artifact_hash:
        return BoundaryVerificationResult(
            passed=False,
            message="Artifact hash mismatch",
            failed_field="artifact_hash",
        )

    receipt_payload = {
        "receipt_id": receipt.receipt_id,
        "timestamp": receipt.timestamp,
        "sender": receipt.sender,
        "receiver": receipt.receiver,
        "artifact_type": receipt.artifact_type,
        "artifact_hash": receipt.artifact_hash,
        "policy_version": receipt.policy_version,
        "verification_status": receipt.verification_status,
        "previous_receipt_hash": receipt.previous_receipt_hash,
    }

    recomputed_receipt_hash = sha256(
        canonical_json(receipt_payload).encode("utf-8")
    ).hexdigest()

    if recomputed_receipt_hash != receipt.current_receipt_hash:
        return BoundaryVerificationResult(
            passed=False,
            message="Boundary Receipt hash mismatch",
            failed_field="current_receipt_hash",
        )

    if expected_sender is not None and receipt.sender != expected_sender:
        return BoundaryVerificationResult(
            passed=False,
            message="Unexpected sender",
            failed_field="sender",
        )

    if expected_receiver is not None and receipt.receiver != expected_receiver:
        return BoundaryVerificationResult(
            passed=False,
            message="Unexpected receiver",
            failed_field="receiver",
        )

    if (
        expected_previous_receipt_hash is not None
        and receipt.previous_receipt_hash
        != expected_previous_receipt_hash
    ):
        return BoundaryVerificationResult(
            passed=False,
            message="Previous receipt reference mismatch",
            failed_field="previous_receipt_hash",
        )

    if receipt.verification_status != "VERIFIED":
        return BoundaryVerificationResult(
            passed=False,
            message="Boundary handoff was not verified",
            failed_field="verification_status",
        )

    return BoundaryVerificationResult(
        passed=True,
        message="Boundary Receipt verified",
    )
