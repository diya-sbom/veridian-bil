from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.trust_root import TrustedKeyRegistry
from executor.executor import ExecutionResult
from executor.execution_evidence import authenticate_execution_result
from mira.state_receipt import create_state_receipt
from bil.state_record import create_state_record
from afs.commit import commit_state


issuer = "VeridianExecutor"
private_key = Ed25519PrivateKey.generate()

registry = TrustedKeyRegistry()
registry.register(
    issuer,
    private_key.public_key(),
)

execution = ExecutionResult(
    execution_id="trusted-execution-001",
    timestamp="2026-10-26T22:45:00+00:00",
    decision_id="trusted-decision-001",
    status="EXECUTED",
    action="EXECUTE_PAYMENT",
    message="Intent executed successfully",
)

execution_evidence = authenticate_execution_result(
    execution,
    issuer,
    private_key,
)

resulting_state = {
    "balance": 500,
    "payment_executed": True,
}

state_receipt = create_state_receipt(
    execution,
    resulting_state,
    execution_evidence,
    registry,
)

state_record = create_state_record(
    state_receipt,
)

commit = commit_state(
    state_record,
    state_receipt,
    execution,
    execution_evidence,
    registry,
)

print("STATE RECEIPT:", state_receipt.to_dict())
print("STATE RECORD:", state_record.to_dict())
print("COMMIT:", commit.to_dict())

assert state_receipt.verification_status == "VERIFIED"
assert state_record.verification_status == "VERIFIED"
assert commit.committed is True

print(
    "PASS: trusted authenticated execution produced "
    "VERIFIED state evidence and committed successfully"
)

print("\n--- EXECUTION / STATE SUBSTITUTION ATTACK ---")

substituted_execution = ExecutionResult(
    execution_id="substituted-execution-999",
    timestamp="2026-10-26T22:46:00+00:00",
    decision_id="substituted-decision-999",
    status="EXECUTED",
    action="EXECUTE_PAYMENT",
    message="Intent executed successfully",
)

unauthorized_state = {
    "balance": 0,
    "payment_executed": True,
}

substituted_state_receipt = create_state_receipt(
    substituted_execution,
    unauthorized_state,
    execution_evidence,
    registry,
)

substituted_state_record = create_state_record(
    substituted_state_receipt,
)

substituted_commit = commit_state(
    substituted_state_record,
    substituted_state_receipt,
    substituted_execution,
    execution_evidence,
    registry,
)

print("SUBSTITUTED STATE RECEIPT:", substituted_state_receipt.to_dict())
print("SUBSTITUTED STATE RECORD:", substituted_state_record.to_dict())
print("SUBSTITUTED COMMIT:", substituted_commit.to_dict())

assert substituted_state_receipt.verification_status == "FAILED"
assert substituted_state_record.verification_status == "FAILED"
assert substituted_commit.committed is False

print(
    "PASS: authenticated evidence for one execution could not be "
    "substituted onto a different execution or committed state"
)
