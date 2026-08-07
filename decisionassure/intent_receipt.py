from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import uuid


@dataclass
class IntentReceipt:
    intent_receipt_id: str
    timestamp: str
    decision_id: str
    boundary_receipt_hash: str
    verification_status: str
    signature: str

    def to_dict(self):
        return self.__dict__


def create_intent_receipt(boundary_receipt, verification_result):

    payload = {
        "decision_id": verification_result.decision_id,
        "boundary_receipt_hash": boundary_receipt.current_receipt_hash,
        "status": verification_result.status,
    }

    signature = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return IntentReceipt(
        intent_receipt_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        decision_id=verification_result.decision_id,
        boundary_receipt_hash=boundary_receipt.current_receipt_hash,
        verification_status=verification_result.status,
        signature=signature,
    )
