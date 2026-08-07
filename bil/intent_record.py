from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import uuid


@dataclass(frozen=True)
class IntentRecord:
    intent_record_id: str
    timestamp: str

    decision_id: str
    governance_receipt_id: str
    boundary_receipt_id: str
    intent_receipt_id: str

    artifact_hash: str

    status: str
    signature: str

    def to_dict(self):
        return self.__dict__


def create_intent_record(
    governance_receipt,
    boundary_receipt,
    intent_receipt,
):
    payload = {
        "decision_id": intent_receipt.decision_id,
        "governance_receipt_id": governance_receipt.decision_id,
        "boundary_receipt_id": boundary_receipt.receipt_id,
        "intent_receipt_id": intent_receipt.intent_receipt_id,
        "status": intent_receipt.verification_status,
    }

    artifact_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    signature = hashlib.sha256(
        artifact_hash.encode()
    ).hexdigest()

    return IntentRecord(
        intent_record_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),

        decision_id=intent_receipt.decision_id,
        governance_receipt_id=governance_receipt.decision_id,
        boundary_receipt_id=boundary_receipt.receipt_id,
        intent_receipt_id=intent_receipt.intent_receipt_id,

        artifact_hash=artifact_hash,

        status=intent_receipt.verification_status,
        signature=signature,
    )
