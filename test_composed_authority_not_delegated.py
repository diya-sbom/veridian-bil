from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import (
    create_intent_receipt,
    verify_intent_receipt,
)
from bil.intent_record import create_intent_record
from bvp.boundary_receipt import create_boundary_receipt
from executor.executor import _execute_verified_intent

from test_capability_acquisition_no_authority_expansion import (
    acquire_intent_receipt,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    trusted_key_registry,
)

from test_agreement_commitment_authority import (
    draft_boundary,
    draft_verification,
)


# ------------------------------------------------------------------
# Component A was independently VERIFIED:
# ACQUIRE_PAYMENT_CAPABILITY
# ------------------------------------------------------------------

assert verify_intent_receipt(acquire_intent_receipt) is True
assert acquire_intent_receipt.verified_action == "ACQUIRE_PAYMENT_CAPABILITY"


# ------------------------------------------------------------------
# Component B was independently VERIFIED:
# DRAFT_AGREEMENT
# ------------------------------------------------------------------

assert draft_verification.status == "VERIFIED"
assert draft_verification.verified_action == "DRAFT_AGREEMENT"

draft_intent_receipt = create_intent_receipt(
    draft_boundary,
    draft_verification,
)

assert verify_intent_receipt(draft_intent_receipt) is True
assert draft_intent_receipt.verified_action == "DRAFT_AGREEMENT"


component_receipts = [
    acquire_intent_receipt,
    draft_intent_receipt,
]

print(
    "VERIFIED COMPONENT ACTIONS:",
    [receipt.verified_action for receipt in component_receipts],
)


# ------------------------------------------------------------------
# Composition attempt:
#
# Both component actions were independently authorized.
# Their combination must NOT manufacture authority to EXECUTE_PAYMENT.
# ------------------------------------------------------------------

composed_decision = create_decision_object(
    requestor="human-001",
    authority="Finance Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent=(
        "Use independently authorized capability acquisition and "
        "agreement operation to execute payment"
    ),
    evidence_references=[
        "capability-evidence-001",
        "agreement-evidence-001",
    ],
    decision="APPROVED",
    intended_action="EXECUTE_PAYMENT",
    intended_state={"status": "PAID"},
    composed_from_actions=[
        "ACQUIRE_PAYMENT_CAPABILITY",
        "DRAFT_AGREEMENT",
    ],
)

composed_gov = create_governance_receipt(composed_decision)

composed_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=composed_decision.to_dict(),
    policy_version="policy-v1",
)

composed_verification = verify_intent(
    composed_decision,
    composed_gov,
    composed_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    trusted_key_registry=trusted_key_registry,
    component_intent_receipts=component_receipts,
)

composed_intent_receipt = create_intent_receipt(
    composed_boundary,
    composed_verification,
)

composed_intent_record = create_intent_record(
    composed_gov,
    composed_boundary,
    composed_intent_receipt,
)

composed_execution = _execute_verified_intent(composed_intent_record)

print("COMPOSED VERIFICATION:", composed_verification.to_dict())
print("COMPOSED EXECUTION:", composed_execution.to_dict())

assert composed_verification.status == "FAILED"
assert (
    composed_verification.reason
    == "COMPOSED_AUTHORITY_NOT_DELEGATED"
)
assert composed_verification.intent_receipt_id is None

assert composed_execution.status == "FAILED_CLOSED"
assert composed_execution.action == "NONE"
assert (
    composed_execution.message
    == "Execution blocked: intent not verified"
)

print(
    "PASS: independently verified component actions did not "
    "manufacture authority for EXECUTE_PAYMENT"
)
