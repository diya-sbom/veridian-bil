from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.responsibility_chain import create_responsibility_chain
from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.diya_adapter import verify_intent

decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Approve deployment",
    evidence_references=["evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status":"ACTIVE"},
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
    state_reference="peer-hijack-authority-state-001",
)

# Peer agent attempts to present otherwise-valid authority evidence.
authority_boundary_receipt = create_boundary_receipt(
    sender="PeerAgent-7",
    receiver="Veridian",
    artifact_type="AUTHORITY_DELEGATION",
    artifact=authority_evidence.to_dict(),
    policy_version="policy-v1",
)

boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=decision.to_dict(),
    policy_version="policy-v1",
)

result = verify_intent(
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

print(result)
print(result.to_dict())

assert result.status == "FAILED"
assert result.reason == "UNAUTHORIZED_DELEGATION"
assert result.intent_receipt_id is None
