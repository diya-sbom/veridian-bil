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

# Delegated authority expires at 23:30 UTC.
responsibility_chain = replace(
    responsibility_chain,
    valid_until="2026-10-12T23:30:00+00:00",
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

# Authority state does not become effective until 23:45 UTC,
# which is after the delegation itself has already expired.
authority_state_evidence, authority_state_boundary_receipt = (
    create_authority_state_fixture(
        responsibility_chain,
        authority_evidence,
        state="ACTIVE",
        effective_at="2026-10-12T23:45:00+00:00",
        state_reference="temporal-non-overlap-001",
    )
)

# CASE 1: before delegation expiry, authority state is not yet effective.
before_expiry = verify_intent(
    decision,
    governance_receipt,
    boundary_receipt,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time=datetime(2026, 10, 12, 23, 20, tzinfo=timezone.utc),
    trusted_key_registry=trusted_key_registry,
)

print("BEFORE EXPIRY:", before_expiry.to_dict())

assert before_expiry.status == "FAILED"
assert before_expiry.reason == "AUTHORITY_STATE_NOT_EFFECTIVE"
assert before_expiry.intent_receipt_id is None

# CASE 2: after delegation expiry but before state effectiveness.
after_expiry = verify_intent(
    decision,
    governance_receipt,
    boundary_receipt,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time=datetime(2026, 10, 12, 23, 40, tzinfo=timezone.utc),
    trusted_key_registry=trusted_key_registry,
)

print("AFTER EXPIRY:", after_expiry.to_dict())

assert after_expiry.status == "FAILED"
assert after_expiry.reason == "EXPIRED_AUTHORITY"
assert after_expiry.intent_receipt_id is None

# CASE 3: even once the state becomes effective, the grant is already expired.
after_state_effective = verify_intent(
    decision,
    governance_receipt,
    boundary_receipt,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time=datetime(2026, 10, 12, 23, 50, tzinfo=timezone.utc),
    trusted_key_registry=trusted_key_registry,
)

print("AFTER STATE EFFECTIVE:", after_state_effective.to_dict())

assert after_state_effective.status == "FAILED"
assert after_state_effective.reason == "EXPIRED_AUTHORITY"
assert after_state_effective.intent_receipt_id is None

print(
    "PASS: non-overlapping delegation and authority-state windows "
    "never create executable authority"
)
