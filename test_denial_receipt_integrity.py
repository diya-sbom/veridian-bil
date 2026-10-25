from copy import deepcopy

from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import (
    create_intent_receipt,
    verify_denial_receipt,
)
from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture


decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Approve deployment",
    evidence_references=["evidence-001"],
    decision="APPROVED",
    intended_action="DELETE",
    intended_state={"status": "ACTIVE"},
)

gov = create_governance_receipt(decision)

(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture()

(
    authority_state_evidence,
    authority_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    state_reference="denial-receipt-state-001",
)

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
    authority_state_evidence,
    authority_state_boundary_receipt,
    trusted_key_registry=trusted_key_registry,
)

assert verification.status == "FAILED"
assert verification.reason == "OUT_OF_SCOPE"
assert verification.intent_receipt_id is None

denial_receipt = create_intent_receipt(boundary, verification)

assert denial_receipt.verification_status == "FAILED"
assert denial_receipt.verified_action is None
assert verify_denial_receipt(denial_receipt) is True

print("PASS: genuine denial receipt independently verifies")

tampered_receipt = deepcopy(denial_receipt)
object.__setattr__(tampered_receipt, "signature", "tampered-signature")

assert verify_denial_receipt(tampered_receipt) is False

print("PASS: tampered denial receipt fails integrity verification")
