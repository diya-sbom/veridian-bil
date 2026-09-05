from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.responsibility_chain import create_responsibility_chain
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

responsibility_chain = create_responsibility_chain(
    organization="Acme Corp",
    business_owner="Alice",
    decision_authority="Risk Committee",
    delegated_by="Alice",
    delegated_to="Veridian",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Deployment Agent",
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
)

print(result)
print(result.to_dict())
