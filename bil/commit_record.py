from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import uuid


@dataclass(frozen=True)
class CommitRecord:
    commit_record_id: str
    timestamp: str

    commit_id: str
    execution_id: str

    commit_hash: str

    signature: str

    def to_dict(self):
        return self.__dict__


def create_commit_record(commit):

    payload = {
        "commit_id": commit.commit_id,
        "execution_id": commit.execution_id,
        "commit_hash": commit.commit_hash,
    }

    artifact_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    signature = hashlib.sha256(
        artifact_hash.encode()
    ).hexdigest()

    return CommitRecord(
        commit_record_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),

        commit_id=commit.commit_id,
        execution_id=commit.execution_id,

        commit_hash=commit.commit_hash,

        signature=signature,
    )
