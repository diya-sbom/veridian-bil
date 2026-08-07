from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Dict, Optional
from uuid import uuid4


VALID_VERIFICATION_STATUSES = {
    "VERIFIED",
    "REJECTED",
    "PENDING",
}


def canonical_json(data: Dict[str, Any]) -> str:
    """Return deterministic JSON for hashing."""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


@dataclass(frozen=True)
class BoundaryReceipt:
    """
    Immutable evidence of a handoff between two protected components.
    """

    receipt_id: str
    timestamp: str
    sender: str
    receiver: str
    artifact_type: str
    artifact_hash: str
    policy_version: str
    verification_status: str
    previous_receipt_hash: Optional[str]
    current_receipt_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def create_boundary_receipt(
    sender: str,
    receiver: str,
    artifact_type: str,
    artifact: Dict[str, Any],
    policy_version: str,
    verification_status: str = "VERIFIED",
    previous_receipt_hash: Optional[str] = None,
) -> BoundaryReceipt:
    """Create a content-addressed Boundary Receipt."""

    if not sender.strip():
        raise ValueError("sender is required")

    if not receiver.strip():
        raise ValueError("receiver is required")

    if not artifact_type.strip():
        raise ValueError("artifact_type is required")

    if not policy_version.strip():
        raise ValueError("policy_version is required")

    if verification_status not in VALID_VERIFICATION_STATUSES:
        raise ValueError(
            "verification_status must be one of: "
            f"{sorted(VALID_VERIFICATION_STATUSES)}"
        )

    receipt_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    artifact_hash = sha256(
        canonical_json(artifact).encode("utf-8")
    ).hexdigest()

    receipt_payload = {
        "receipt_id": receipt_id,
        "timestamp": timestamp,
        "sender": sender,
        "receiver": receiver,
        "artifact_type": artifact_type,
        "artifact_hash": artifact_hash,
        "policy_version": policy_version,
        "verification_status": verification_status,
        "previous_receipt_hash": previous_receipt_hash,
    }

    current_receipt_hash = sha256(
        canonical_json(receipt_payload).encode("utf-8")
    ).hexdigest()

    return BoundaryReceipt(
        receipt_id=receipt_id,
        timestamp=timestamp,
        sender=sender,
        receiver=receiver,
        artifact_type=artifact_type,
        artifact_hash=artifact_hash,
        policy_version=policy_version,
        verification_status=verification_status,
        previous_receipt_hash=previous_receipt_hash,
        current_receipt_hash=current_receipt_hash,
    )
