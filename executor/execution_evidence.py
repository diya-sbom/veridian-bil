from dataclasses import dataclass
from typing import Dict, Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.trust_root import (
    TrustedKeyRegistry,
    public_key_id,
    sign_payload,
)


@dataclass(frozen=True)
class AuthenticatedExecutionEvidence:
    execution_id: str
    timestamp: str
    decision_id: str
    status: str
    action: str
    message: str
    executor_issuer: str
    executor_key_id: str
    executor_signature: str

    def to_dict(self):
        return self.__dict__


def execution_payload(execution_result) -> Dict[str, Any]:
    return {
        "execution_id": execution_result.execution_id,
        "timestamp": execution_result.timestamp,
        "decision_id": execution_result.decision_id,
        "status": execution_result.status,
        "action": execution_result.action,
        "message": execution_result.message,
    }


def authenticate_execution_result(
    execution_result,
    executor_issuer: str,
    private_key: Ed25519PrivateKey,
) -> AuthenticatedExecutionEvidence:
    if not isinstance(executor_issuer, str) or not executor_issuer.strip():
        raise ValueError("executor_issuer must be a non-empty string")

    key_id = public_key_id(private_key.public_key())
    payload = execution_payload(execution_result)
    signature = sign_payload(private_key, payload)

    return AuthenticatedExecutionEvidence(
        execution_id=execution_result.execution_id,
        timestamp=execution_result.timestamp,
        decision_id=execution_result.decision_id,
        status=execution_result.status,
        action=execution_result.action,
        message=execution_result.message,
        executor_issuer=executor_issuer,
        executor_key_id=key_id,
        executor_signature=signature,
    )


def verify_execution_evidence(
    evidence: AuthenticatedExecutionEvidence,
    execution_result,
    registry: TrustedKeyRegistry,
) -> bool:
    expected_payload = execution_payload(execution_result)

    evidence_payload = {
        "execution_id": evidence.execution_id,
        "timestamp": evidence.timestamp,
        "decision_id": evidence.decision_id,
        "status": evidence.status,
        "action": evidence.action,
        "message": evidence.message,
    }

    if evidence_payload != expected_payload:
        return False

    return registry.verify(
        evidence.executor_issuer,
        evidence.executor_key_id,
        evidence_payload,
        evidence.executor_signature,
    )
