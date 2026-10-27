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


def commit_state(
    state_record,
    state_receipt,
    execution,
    execution_evidence=None,
    trusted_key_registry=None,
):
    from executor.execution_evidence import verify_execution_evidence

    state_receipt_hash = hashlib.sha256(
        json.dumps(state_receipt.state, sort_keys=True).encode()
    ).hexdigest() if state_receipt is not None else None

    expected_state_receipt_signature = (
        hashlib.sha256(
            (state_receipt.execution_id + state_receipt_hash).encode()
        ).hexdigest()
        if state_receipt is not None
        else None
    )

    state_record_payload = (
        {
            "execution_id": state_record.execution_id,
            "state_receipt_id": state_record.state_receipt_id,
            "state_hash": state_record.state_hash,
            "verification_status": state_record.verification_status,
        }
        if state_record is not None
        else None
    )

    expected_state_record_hash = (
        hashlib.sha256(
            json.dumps(state_record_payload, sort_keys=True).encode()
        ).hexdigest()
        if state_record_payload is not None
        else None
    )

    expected_state_record_signature = (
        hashlib.sha256(expected_state_record_hash.encode()).hexdigest()
        if expected_state_record_hash is not None
        else None
    )

    execution_authenticated = (
        execution is not None
        and execution_evidence is not None
        and trusted_key_registry is not None
        and verify_execution_evidence(
            execution_evidence,
            execution,
            trusted_key_registry,
        )
    )

    evidence_valid = (
        execution_authenticated
        and state_receipt is not None
        and state_record is not None
        and getattr(execution, "status", None) == "EXECUTED"
        and state_receipt.execution_id == execution.execution_id
        and state_receipt.state_hash == state_receipt_hash
        and state_receipt.signature == expected_state_receipt_signature
        and state_receipt.verification_status == "VERIFIED"
        and state_record.signature == expected_state_record_signature
        and state_record.execution_id == state_receipt.execution_id
        and state_record.state_receipt_id == state_receipt.state_receipt_id
        and state_record.state_hash == state_receipt.state_hash
        and state_record.verification_status == "VERIFIED"
    )

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
        committed=evidence_valid,
        commit_hash=commit_hash,
        signature=signature,
    )
