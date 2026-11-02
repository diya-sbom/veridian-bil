from datetime import datetime, timezone
from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from decisionassure.decision_replay import replay_denied_decision
from bil.intent_record import create_intent_record
from bvp.boundary_receipt import create_boundary_receipt
from executor.executor import _execute_verified_intent
from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture


# Adversarial class:
# UNTRUSTED_SELLER_INDUCES_ADDITIONAL_PAYMENT
#
# The buyer delegates bounded payment authority.
# A legitimate payment succeeds.
# The seller then induces an additional charge that exceeds remaining authority.
# Seller instructions do not manufacture new payment authority.

(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    decision_authority="Treasury Committee",
    authority_scope="Payment Operations",
    agent="Payment Agent",
    policy_reference="policy-ref-seller-payment-001",
    evidence_reference="signed-payment-mandate-seller-001",
    governed_resource="seller-A",
)


def verify_and_execute(decision, state_evidence, state_boundary):
    gov = create_governance_receipt(decision)

    boundary = create_boundary_receipt(
        sender="DecisionAssure",
        receiver="Diya",
        artifact_type="GOVERNANCE_DECISION",
        artifact=decision.to_dict(),
        policy_version="policy-v1",
    )

    verification = verify_intent(
        decision,
        gov,
        boundary,
        responsibility_chain,
        authority_evidence,
        authority_boundary_receipt,
        authority_state_evidence=state_evidence,
        authority_state_boundary_receipt=state_boundary,
        trusted_key_registry=trusted_key_registry,
    )

    intent_receipt = create_intent_receipt(boundary, verification)
    intent_record = create_intent_record(
        gov,
        boundary,
        intent_receipt,
    )

    execution = _execute_verified_intent(intent_record)

    return gov, boundary, verification, execution


# ============================================================
# CASE 1
# Buyer has 500 USD total delegated authority.
# A legitimate 50 USD payment to seller-A is authorized.
# ============================================================

(
    initial_state,
    initial_state_boundary,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    aggregate_limit=500,
    consumed_units=0,
    authority_unit="USD",
    state_reference="seller-payment-active-001",
)

authorized_payment = create_decision_object(
    requestor="trusted-payment-agent-001",
    authority="Treasury Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Pay seller-A the authorized 50 USD",
    evidence_references=["signed-payment-mandate-seller-001"],
    decision="APPROVED",
    intended_action="EXECUTE_PAYMENT",
    intended_state={"status": "PAYMENT_REQUESTED"},
    requested_authority_units=50,
    requested_authority_unit="USD",
    governed_resource="seller-A",
)

(
    authorized_gov,
    authorized_boundary,
    authorized_verification,
    authorized_execution,
) = verify_and_execute(
    authorized_payment,
    initial_state,
    initial_state_boundary,
)

print("AUTHORIZED PAYMENT VERIFICATION:", authorized_verification.to_dict())
print("AUTHORIZED PAYMENT EXECUTION:", authorized_execution.to_dict())

assert authorized_verification.status == "VERIFIED"
assert authorized_verification.verified_action == "EXECUTE_PAYMENT"
assert authorized_execution.status == "EXECUTED"
assert authorized_execution.action == "EXECUTE_PAYMENT"

account_state = {
    "balance": 1000,
    "paid_to_seller_A": 0,
}

if authorized_execution.status == "EXECUTED":
    account_state["balance"] -= 50
    account_state["paid_to_seller_A"] += 50

assert account_state == {
    "balance": 950,
    "paid_to_seller_A": 50,
}

print("AUTHORIZED 50 USD PAYMENT COMPLETED")


# ============================================================
# CASE 2
# Seller induces an additional 500 USD payment.
#
# The first 50 USD has already consumed part of the mandate.
# Only 450 USD remains.
# Seller request/instruction is not authority.
# ============================================================

(
    post_payment_state,
    post_payment_state_boundary,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    aggregate_limit=500,
    consumed_units=50,
    authority_unit="USD",
    state_reference="seller-payment-after-authorized-001",
)

seller_induced_payment = create_decision_object(
    requestor="trusted-payment-agent-001",
    authority="Treasury Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Seller requests an additional 500 USD payment",
    evidence_references=[
        "signed-payment-mandate-seller-001",
        "seller-additional-payment-request-001",
    ],
    decision="APPROVED",
    intended_action="EXECUTE_PAYMENT",
    intended_state={"status": "ADDITIONAL_PAYMENT_REQUESTED"},
    requested_authority_units=500,
    requested_authority_unit="USD",
    governed_resource="seller-A",
)

(
    seller_gov,
    seller_boundary,
    seller_verification,
    seller_execution,
) = verify_and_execute(
    seller_induced_payment,
    post_payment_state,
    post_payment_state_boundary,
)

print("SELLER-INDUCED PAYMENT VERIFICATION:", seller_verification.to_dict())
print("SELLER-INDUCED PAYMENT EXECUTION:", seller_execution.to_dict())

assert seller_verification.status == "FAILED"
assert seller_verification.reason == "CUMULATIVE_AUTHORITY_EXHAUSTED"
assert seller_verification.intent_receipt_id is None
assert seller_verification.verified_action is None

assert seller_execution.status == "FAILED_CLOSED"
assert seller_execution.action == "NONE"
assert seller_execution.message == "Execution blocked: intent not verified"

# No additional funds move after denial.
assert account_state == {
    "balance": 950,
    "paid_to_seller_A": 50,
}

print("NO ADDITIONAL FUNDS TRANSFERRED")


# ============================================================
# CASE 3
# Independently reproduce the denial from preserved evidence.
# ============================================================

replay_result = replay_denied_decision(
    decision=seller_induced_payment,
    governance_receipt=seller_gov,
    responsibility_chain=responsibility_chain,
    boundary_receipt=seller_boundary,
    boundary_artifact=seller_induced_payment.to_dict(),
    authority_evidence=authority_evidence,
    authority_boundary_receipt=authority_boundary_receipt,
    authority_state_evidence=post_payment_state,
    authority_state_boundary_receipt=post_payment_state_boundary,
    execution_time=datetime.now(timezone.utc),
    expected_failed_condition="CUMULATIVE_AUTHORITY_EXHAUSTED",
    trusted_key_registry=trusted_key_registry,
)

print("SELLER-INDUCED PAYMENT DENIAL REPLAY:", replay_result.to_dict())

assert replay_result.passed is True
assert (
    replay_result.message
    == "Authority denial independently reproduced: CUMULATIVE_AUTHORITY_EXHAUSTED"
)

print(
    "PASS: an untrusted seller request did not expand bounded payment authority; "
    "only the originally authorized payment was transferred"
)
