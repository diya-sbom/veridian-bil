from bil.state_record import StateRecord
from afs.commit import commit_state


# Mandatory upstream evidence is intentionally absent:
# no execution result
# no StateReceipt
# no valid StateRecord signature chain

forged_state_record = StateRecord(
    state_record_id="forged-state-record-001",
    timestamp="2026-10-25T21:45:00+00:00",
    execution_id="unproven-execution-001",
    state_receipt_id="missing-state-receipt-001",
    state_hash="fabricated-state-hash",
    verification_status="VERIFIED",
    signature="invalid-forged-signature",
)

commit = commit_state(forged_state_record, None, None)

print("FORGED STATE RECORD:", forged_state_record.to_dict())
print("COMMIT:", commit.to_dict())

assert forged_state_record.verification_status == "VERIFIED"
assert forged_state_record.signature == "invalid-forged-signature"

# Remediation expectation: missing mandatory evidence must fail closed.
assert commit.committed is False

print(
    "PASS: caller-supplied VERIFIED StateRecord could not replace "
    "missing mandatory evidence; commitment was blocked"
)
