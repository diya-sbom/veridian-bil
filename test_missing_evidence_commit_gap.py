from dataclasses import dataclass

from mira.state_receipt import create_state_receipt
from bil.state_record import create_state_record
from afs.commit import commit_state


@dataclass(frozen=True)
class FakeFailedExecution:
    execution_id: str
    status: str
    action: str


failed_execution = FakeFailedExecution(
    execution_id="failed-execution-001",
    status="FAILED_CLOSED",
    action="NONE",
)

unauthorized_state = {
    "balance": 500,
    "payment_executed": True,
}

state_receipt = create_state_receipt(
    failed_execution,
    unauthorized_state,
)

state_record = create_state_record(
    state_receipt,
)

commit = commit_state(
    state_record,
    state_receipt,
    failed_execution,
)

print("FAILED EXECUTION:", failed_execution)
print("STATE RECEIPT:", state_receipt.to_dict())
print("STATE RECORD:", state_record.to_dict())
print("COMMIT:", commit.to_dict())

assert failed_execution.status == "FAILED_CLOSED"

# Remediation expectations: failed execution must propagate fail-closed.
assert state_receipt.verification_status == "FAILED"
assert state_record.verification_status == "FAILED"
assert commit.committed is False

print(
    "PASS: FAILED_CLOSED execution produced FAILED state evidence "
    "and commitment was blocked"
)
