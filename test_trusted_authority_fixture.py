from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture

from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.diya_adapter import verify_intent
from bvp.boundary_receipt import create_boundary_receipt
from bvp.trust_root import verify_boundary_receipt_authenticity


(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture()


# First prove the authority boundary itself is genuinely authenticated.
assert verify_boundary_receipt_authenticity(
    authority_boundary_receipt,
    trusted_key_registry,
) is True

print("PASS: trusted authority fixture produced authenticated boundary")


authority_state_evidence, authority_state_boundary_receipt = (
    create_authority_state_fixture(
        responsibility_chain,
        authority_evidence,
        state="ACTIVE",
        state_reference="trusted-authority-state-001",
    )
)


decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Deploy application",
    evidence_references=["deployment-evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "DEPLOYED"},
)


governance_receipt = create_governance_receipt(decision)

boundary_receipt = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=decision.to_dict(),
    policy_version="policy-v1",
)


verification = verify_intent(
    decision,
    governance_receipt,
    boundary_receipt,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    trusted_key_registry=trusted_key_registry,
)

print("TRUSTED AUTHORITY VERIFICATION:", verification.to_dict())

assert verification.status == "VERIFIED"
assert verification.intent_receipt_id is not None
assert verification.verified_action == "DEPLOY"

print("PASS: trusted authority registry propagated through verify_intent")
