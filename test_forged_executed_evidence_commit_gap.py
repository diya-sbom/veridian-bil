from executor.executor import ExecutionResult
from mira.state_receipt import create_state_receipt
from bil.state_record import create_state_record
from afs.commit import commit_state


# No real executor invocation occurs.
# The caller fabricates an apparently successful execution object.
forged_execution = ExecutionResult(
    execution_id="forged-execution-001",
    timestamp="2026-10-26T22:00:00+00:00",
    decision_id="unproven-decision-001",
    status="EXECUTED",
    action="EXECUTE_PAYMENT",
    message="fabricated successful execution",
)

forged_resulting_state = {
    "balance": 500,
    "payment_executed": True,
}

state_receipt = create_state_receipt(
    forged_execution,
    forged_resulting_state,
)

state_record = create_state_record(
    state_receipt,
)

commit = commit_state(
    state_record,
    state_receipt,
    forged_execution,
)

print("FORGED EXECUTION:", forged_execution.to_dict())
print("STATE RECEIPT:", state_receipt.to_dict())
print("STATE RECORD:", state_record.to_dict())
print("COMMIT:", commit.to_dict())

assert forged_execution.status == "EXECUTED"
assert state_receipt.verification_status == "FAILED"
assert state_record.verification_status == "FAILED"
assert commit.committed is False

print(
    "PASS: caller-fabricated EXECUTED evidence failed closed "
    "before VERIFIED state evidence and commitment"
)
