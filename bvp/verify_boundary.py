from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, Optional

from bvp.boundary_receipt import BoundaryReceipt, canonical_json
from bvp.trust_root import (
    TrustedKeyRegistry,
    verify_boundary_receipt_authenticity,
)


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
    expected_artifact_type: Optional[str] = None,
    expected_policy_version: Optional[str] = None,
    expected_previous_receipt_hash: Optional[str] = None,
    trusted_key_registry: Optional[TrustedKeyRegistry] = None,
    require_authenticity: bool = False,
) -> BoundaryVerificationResult:
    """
    Independently verify deterministic properties of a Boundary Receipt.

    Verification confirms:
    - artifact integrity against the recorded artifact hash;
    - receipt integrity against the recorded receipt hash;
    - recorded sender and receiver identifiers match expected identifiers;
    - optional artifact type and policy version match expected values;
    - optional receipt-chain linkage matches the expected previous receipt hash;
    - the recorded verification_status is VERIFIED.

    Assumes:
    - expected identifiers and policy values are supplied from a trusted context.

    Does not by itself establish:
    - cryptographic authentication of the sender or receiver;
    - that the recorded sender actually originated the artifact or receipt;
    - that verification_status=VERIFIED is truthful merely because it is recorded;
    - that the underlying action was authorized or otherwise admissible.

    Receipt verification proves integrity and expected-field continuity,
    not external identity, authority, or truth.
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

    if require_authenticity:
        if trusted_key_registry is None:
            return BoundaryVerificationResult(
                passed=False,
                message="Trusted key registry is required",
                failed_field="trusted_key_registry",
            )

        if receipt.issuer_key_id is None or receipt.issuer_signature is None:
            return BoundaryVerificationResult(
                passed=False,
                message="Boundary Receipt is not cryptographically authenticated",
                failed_field="issuer_signature",
            )

        if not verify_boundary_receipt_authenticity(
            receipt,
            trusted_key_registry,
        ):
            return BoundaryVerificationResult(
                passed=False,
                message="Boundary Receipt authenticity verification failed",
                failed_field="issuer_authenticity",
            )

    elif (
        trusted_key_registry is not None
        and receipt.issuer_key_id is not None
        and receipt.issuer_signature is not None
        and not verify_boundary_receipt_authenticity(
            receipt,
            trusted_key_registry,
        )
    ):
        return BoundaryVerificationResult(
            passed=False,
            message="Boundary Receipt authenticity verification failed",
            failed_field="issuer_authenticity",
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
        expected_artifact_type is not None
        and receipt.artifact_type != expected_artifact_type
    ):
        return BoundaryVerificationResult(
            passed=False,
            message="Unexpected artifact type",
            failed_field="artifact_type",
        )

    if (
        expected_policy_version is not None
        and receipt.policy_version != expected_policy_version
    ):
        return BoundaryVerificationResult(
            passed=False,
            message="Unexpected policy version",
            failed_field="policy_version",
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
