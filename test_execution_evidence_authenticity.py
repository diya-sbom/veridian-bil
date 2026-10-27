from dataclasses import replace

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.trust_root import TrustedKeyRegistry
from executor.executor import ExecutionResult
from executor.execution_evidence import (
    authenticate_execution_result,
    verify_execution_evidence,
)


issuer = "VeridianExecutor"

private_key = Ed25519PrivateKey.generate()

registry = TrustedKeyRegistry()
key_id = registry.register(
    issuer,
    private_key.public_key(),
)

execution = ExecutionResult(
    execution_id="execution-auth-001",
    timestamp="2026-10-26T22:30:00+00:00",
    decision_id="decision-auth-001",
    status="EXECUTED",
    action="EXECUTE_PAYMENT",
    message="Intent executed successfully",
)

evidence = authenticate_execution_result(
    execution,
    issuer,
    private_key,
)

assert evidence.executor_key_id == key_id

assert verify_execution_evidence(
    evidence,
    execution,
    registry,
) is True

print("PASS: trusted executor execution evidence verifies")


tampered_execution = replace(
    execution,
    action="DEPLOY",
)

assert verify_execution_evidence(
    evidence,
    tampered_execution,
    registry,
) is False

print("PASS: execution action tampering is detected")


unknown_registry = TrustedKeyRegistry()

assert verify_execution_evidence(
    evidence,
    execution,
    unknown_registry,
) is False

print("PASS: unknown executor key is denied")


registry.revoke(
    issuer,
    key_id,
)

assert verify_execution_evidence(
    evidence,
    execution,
    registry,
) is False

print("PASS: revoked executor key is denied")
