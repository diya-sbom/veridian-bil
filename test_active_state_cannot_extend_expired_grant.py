from dataclasses import replace
from datetime import datetime, timezone

from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.diya_adapter import verify_intent
from bvp.boundary_receipt import create_boundary_receipt


(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture()

# Delegation expires at 00:30 UTC.
responsibility_chain = replace(
    responsibility_chain,
    valid_until="2026-10-13T00:30:00+00:00",
)

decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Approve controlled deployment",
    evidence_references=["evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "ACTIVE"},
)

governance_receipt = create_governance_receipt(decision)

boundary_receipt = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=decision.to_dict(),
    policy_version="policy-v1",
)

# Authority state became ACTIVE before the delegation expires.
authority_state_evidence, authority_state_boundary_receipt = (
    create_authority_state_fixture(
        responsibility_chain,
        authority_evidence,
        state="ACTIVE",
        effective_at="2026-10-12T23:30:00+00:00",
        state_reference="active-before-expiry-001",
    )
)

# CASE 1: while the grant is still valid, ACTIVE state permits verification.
before_expiry = verify_intent(
    decision,
    governance_receipt,
    boundary_receipt,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time=datetime(2026, 10, 13, 0, 0, tzinfo=timezone.utc),
    trusted_key_registry=trusted_key_registry,
)

print("BEFORE EXPIRY:", before_expiry.to_dict())

assert before_expiry.status == "VERIFIED"
assert before_expiry.intent_receipt_id is not None
assert before_expiry.verified_action == "DEPLOY"

# CASE 2: the same ACTIVE state must not extend authority past grant expiry.
after_expiry = verify_intent(
    decision,
    governance_receipt,
    boundary_receipt,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time=datetime(2026, 10, 13, 0, 40, tzinfo=timezone.utc),
    trusted_key_registry=trusted_key_registry,
)

print("AFTER EXPIRY:", after_expiry.to_dict())

assert after_expiry.status == "FAILED"
assert after_expiry.reason == "EXPIRED_AUTHORITY"
assert after_expiry.intent_receipt_id is None
assert after_expiry.verified_action is None

print(
    "PASS: previously active authority state did not extend "
    "delegated authority beyond grant expiry"
)
