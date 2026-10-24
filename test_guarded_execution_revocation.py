from datetime import datetime, timezone

from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from bil.intent_record import create_intent_record
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.decision_object import create_decision_object
from decisionassure.diya_adapter import verify_intent
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.intent_receipt import create_intent_receipt
from executor.executor import execute_intent
from executor.guarded_execution import execute_with_current_authority


(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    decision_authority="Treasury Committee",
    authority_scope="Payment Operations",
    agent="Payment Agent",
    policy_reference="policy-ref-payment-001",
    evidence_reference="signed-payment-mandate-001",
    governed_resource="payee-A",
)

(
    active_state,
    active_state_boundary,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    effective_at="2026-10-22T22:00:00+00:00",
    aggregate_limit=500,
    consumed_units=0,
    authority_unit="USD",
    state_reference="payment-active-state-001",
)

authorization_time = datetime(2026, 10, 22, 22, 30, tzinfo=timezone.utc)

payment = create_decision_object(
    requestor="trusted-payment-agent-001",
    authority="Treasury Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Execute exact authorized payment",
    evidence_references=["signed-payment-mandate-001"],
    decision="APPROVED",
    intended_action="EXECUTE_PAYMENT",
    intended_state={"status": "PAYMENT_REQUESTED"},
    requested_authority_units=500,
    requested_authority_unit="USD",
    governed_resource="payee-A",
)

gov = create_governance_receipt(payment)

boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=payment.to_dict(),
    policy_version="policy-v1",
)

verification = verify_intent(
    payment,
    gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    active_state,
    active_state_boundary,
    execution_time=authorization_time,
    trusted_key_registry=trusted_key_registry,
)

assert verification.status == "VERIFIED"
assert verification.verified_action == "EXECUTE_PAYMENT"

intent_receipt = create_intent_receipt(boundary, verification)

intent_record = create_intent_record(
    gov,
    boundary,
    intent_receipt,
)

print("PRE-REVOCATION INTENT RECORD STATUS:", intent_record.status)
print("PRE-REVOCATION VERIFIED ACTION:", intent_record.verified_action)

# Positive control:
# Current ACTIVE authority must still permit the exact authorized payment.
(
    active_reverification,
    active_fresh_receipt,
    active_fresh_record,
    active_execution,
) = execute_with_current_authority(
    payment,
    gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    active_state,
    active_state_boundary,
    authorization_time,
    trusted_key_registry,
)

print("ACTIVE EXECUTION-TIME REVALIDATION:", active_reverification.to_dict())
print("ACTIVE GUARDED EXECUTION:", active_execution.to_dict())

assert active_reverification.status == "VERIFIED"
assert active_reverification.verified_action == "EXECUTE_PAYMENT"
assert active_execution.status == "EXECUTED"
assert active_execution.action == "EXECUTE_PAYMENT"

print("PASS: current ACTIVE authority still executes through guarded boundary")

# Authority is revoked AFTER the executable IntentRecord was issued.
revocation_time = "2026-10-22T22:31:00+00:00"

(
    revoked_state,
    revoked_state_boundary,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="REVOKED",
    effective_at=revocation_time,
    aggregate_limit=500,
    consumed_units=0,
    authority_unit="USD",
    state_reference="payment-revoked-state-001",
)

assert revoked_state.state == "REVOKED"

# Critical regression step:
# The OLD IntentRecord exists, but execution must revalidate CURRENT authority.
execution_time = datetime(2026, 10, 22, 22, 32, tzinfo=timezone.utc)

(
    fresh_verification,
    fresh_intent_receipt,
    fresh_intent_record,
    execution,
) = execute_with_current_authority(
    payment,
    gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    revoked_state,
    revoked_state_boundary,
    execution_time,
    trusted_key_registry,
)

print("EXECUTION-TIME REVALIDATION:", fresh_verification.to_dict())
print("GUARDED EXECUTION:", execution.to_dict())

assert fresh_verification.status == "FAILED"
assert fresh_verification.reason == "REVOKED_AUTHORITY"
assert fresh_verification.intent_receipt_id is None

assert fresh_intent_receipt.verification_status == "FAILED"
assert fresh_intent_receipt.verified_action is None

assert fresh_intent_record.status == "FAILED"
assert fresh_intent_record.verified_action is None

assert execution.status == "FAILED_CLOSED"
assert execution.action == "NONE"
assert execution.message == "Execution blocked: intent not verified"

print(
    "PASS: stale previously VERIFIED payment did not survive "
    "execution-time authority revalidation"
)
