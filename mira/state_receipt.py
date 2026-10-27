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


def create_state_receipt(
    execution_result,
    state,
    execution_evidence=None,
    trusted_key_registry=None,
):
    from executor.execution_evidence import verify_execution_evidence

    state_hash = hashlib.sha256(
        json.dumps(state, sort_keys=True).encode()
    ).hexdigest()

    signature = hashlib.sha256(
        (execution_result.execution_id + state_hash).encode()
    ).hexdigest()

    execution_authenticated = (
        execution_evidence is not None
        and trusted_key_registry is not None
        and verify_execution_evidence(
            execution_evidence,
            execution_result,
            trusted_key_registry,
        )
    )

    verification_status = (
        "VERIFIED"
        if (
            getattr(execution_result, "status", None) == "EXECUTED"
            and execution_authenticated
        )
        else "FAILED"
    )

    return StateReceipt(
        state_receipt_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        execution_id=execution_result.execution_id,
        state_hash=state_hash,
        state=state,
        verification_status=verification_status,
        signature=signature,
    )
