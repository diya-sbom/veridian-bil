from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import uuid


@dataclass(frozen=True)
class StateReceipt:
    state_receipt_id: str
    timestamp: str
    execution_id: str
    state_hash: str
    state: dict
    verification_status: str
    signature: str

    def to_dict(self):
        return self.__dict__


def create_state_receipt(execution_result, state):
    state_hash = hashlib.sha256(
        json.dumps(state, sort_keys=True).encode()
    ).hexdigest()

    signature = hashlib.sha256(
        (execution_result.execution_id + state_hash).encode()
    ).hexdigest()

    return StateReceipt(
        state_receipt_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        execution_id=execution_result.execution_id,
        state_hash=state_hash,
        state=state,
        verification_status="VERIFIED",
        signature=signature,
    )
