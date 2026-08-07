from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import uuid


@dataclass(frozen=True)
class CommitReceipt:
    commit_id: str
    timestamp: str

    state_record_id: str
    execution_id: str

    committed: bool

    commit_hash: str
    signature: str

    def to_dict(self):
        return self.__dict__


def commit_state(state_record):

    payload = {
        "state_record_id": state_record.state_record_id,
        "execution_id": state_record.execution_id,
        "state_hash": state_record.state_hash,
        "verification_status": state_record.verification_status,
    }

    commit_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    signature = hashlib.sha256(
        commit_hash.encode()
    ).hexdigest()

    return CommitReceipt(
        commit_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),

        state_record_id=state_record.state_record_id,
        execution_id=state_record.execution_id,

        committed=True,

        commit_hash=commit_hash,
        signature=signature,
    )
