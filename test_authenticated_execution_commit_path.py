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
