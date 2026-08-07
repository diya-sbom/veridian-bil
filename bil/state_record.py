from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import uuid


@dataclass(frozen=True)
class StateRecord:
    state_record_id: str
    timestamp: str

    execution_id: str
    state_receipt_id: str

    state_hash: str

    verification_status: str

    signature: str

    def to_dict(self):
        return self.__dict__


def create_state_record(state_receipt):

    payload = {
        "execution_id": state_receipt.execution_id,
        "state_receipt_id": state_receipt.state_receipt_id,
        "state_hash": state_receipt.state_hash,
        "verification_status": state_receipt.verification_status,
    }

    artifact_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    signature = hashlib.sha256(
        artifact_hash.encode()
    ).hexdigest()

    return StateRecord(
        state_record_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),

        execution_id=state_receipt.execution_id,
        state_receipt_id=state_receipt.state_receipt_id,

        state_hash=state_receipt.state_hash,

        verification_status=state_receipt.verification_status,

        signature=signature,
    )
