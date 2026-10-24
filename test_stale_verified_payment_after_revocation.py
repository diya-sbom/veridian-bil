from datetime import datetime, timezone

from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from bil.intent_record import create_intent_record
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.decision_object import create_decision_object
from decisionassure.diya_adapter import verify_intent
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.intent_receipt import create_intent_receipt
from executor.executor import _execute_verified_intent


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

# Critical adversarial step:
# present the OLD, untouched VERIFIED IntentRecord directly to executor.
execution = _execute_verified_intent(intent_record)

print("POST-REVOCATION STALE EXECUTION:", execution.to_dict())

# This assertion records the CURRENT unsafe behavior.
# If this test stops passing after enforcement is fixed, that is expected.
assert execution.status == "EXECUTED"
assert execution.action == "EXECUTE_PAYMENT"

print(
    "GAP CONFIRMED: previously VERIFIED payment IntentRecord "
    "still executes after authority revocation"
)
