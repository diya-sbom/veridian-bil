from datetime import datetime, timezone

from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.responsibility_chain import create_responsibility_chain
from decisionassure.authority_delegation import create_authority_delegation_evidence
from decisionassure.diya_adapter import verify_intent
from bvp.boundary_receipt import create_boundary_receipt
from authority_state_fixture import create_authority_state_fixture


execution_time = datetime.now(timezone.utc)


# Root authority:
# Alice delegates Production Deployment authority on service-A to Parent-Agent.
parent_authority_evidence = create_authority_delegation_evidence(
    delegator="Alice",
    delegatee="Parent-Agent",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    policy_reference="policy-ref-deploy-001",
    evidence_reference="parent-authority-001",
    delegation_status="AUTHORIZED",
    governed_resource="service-A",
)

parent_authority_boundary = create_boundary_receipt(
    sender="AuthorityService",
    receiver="Veridian",
    artifact_type="AUTHORITY_DELEGATION",
    artifact=parent_authority_evidence.to_dict(),
    policy_version="policy-v1",
)


# ------------------------------------------------------------------
# CASE 1: valid child delegation
# Parent-Agent delegates the SAME bounded authority to Subagent-A.
# ------------------------------------------------------------------

valid_chain = create_responsibility_chain(
    organization="Acme Corp",
    business_owner="Alice",
    decision_authority="Operations Committee",
    delegated_by="Parent-Agent",
    delegated_to="Subagent-A",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Subagent-A",
    policy_reference="policy-ref-deploy-001",
    evidence_reference="child-authority-valid-001",
    authority_evidence_source="AuthorityService",
)

valid_child_evidence = create_authority_delegation_evidence(
    delegator="Parent-Agent",
    delegatee="Subagent-A",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    policy_reference="policy-ref-deploy-001",
    evidence_reference="child-authority-valid-001",
    delegation_status="AUTHORIZED",
    governed_resource="service-A",
    parent_authority_evidence_hash=parent_authority_evidence.evidence_hash,
)

valid_authority_boundary = create_boundary_receipt(
    sender="AuthorityService",
    receiver="Veridian",
    artifact_type="AUTHORITY_DELEGATION",
    artifact=valid_child_evidence.to_dict(),
    policy_version="policy-v1",
)

valid_state, valid_state_boundary = create_authority_state_fixture(
    valid_chain,
    valid_child_evidence,
    state="ACTIVE",
    effective_at=execution_time.isoformat(),
    state_reference="child-state-valid-001",
)

valid_decision = create_decision_object(
    requestor="human-001",
    authority="Operations Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Deploy application through authorized subagent",
    evidence_references=["deployment-evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "DEPLOYED"},
    governed_resource="service-A",
)

valid_gov = create_governance_receipt(valid_decision)

valid_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Veridian",
    artifact_type="DECISION_OBJECT",
    artifact=valid_decision.to_dict(),
    policy_version="policy-v1",
)

valid_result = verify_intent(
    valid_decision,
    valid_gov,
    valid_boundary,
    valid_chain,
    valid_child_evidence,
    valid_authority_boundary,
    authority_state_evidence=valid_state,
    authority_state_boundary_receipt=valid_state_boundary,
    execution_time=execution_time,
    parent_authority_evidence=parent_authority_evidence,
    parent_authority_boundary_receipt=parent_authority_boundary,
)

print("VALID CHILD DELEGATION:", valid_result.to_dict())

assert valid_result.status == "VERIFIED"
assert valid_result.intent_receipt_id is not None
assert valid_result.verified_action == "DEPLOY"


# ------------------------------------------------------------------
# CASE 2: child attempts authority expansion to service-B
# ------------------------------------------------------------------

invalid_chain = create_responsibility_chain(
    organization="Acme Corp",
    business_owner="Alice",
    decision_authority="Operations Committee",
    delegated_by="Parent-Agent",
    delegated_to="Subagent-A",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Subagent-A",
    policy_reference="policy-ref-deploy-001",
    evidence_reference="child-authority-invalid-001",
    authority_evidence_source="AuthorityService",
)

invalid_child_evidence = create_authority_delegation_evidence(
    delegator="Parent-Agent",
    delegatee="Subagent-A",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    policy_reference="policy-ref-deploy-001",
    evidence_reference="child-authority-invalid-001",
    delegation_status="AUTHORIZED",
    governed_resource="service-B",
    parent_authority_evidence_hash=parent_authority_evidence.evidence_hash,
)

invalid_authority_boundary = create_boundary_receipt(
    sender="AuthorityService",
    receiver="Veridian",
    artifact_type="AUTHORITY_DELEGATION",
    artifact=invalid_child_evidence.to_dict(),
    policy_version="policy-v1",
)

invalid_state, invalid_state_boundary = create_authority_state_fixture(
    invalid_chain,
    invalid_child_evidence,
    state="ACTIVE",
    effective_at=execution_time.isoformat(),
    state_reference="child-state-invalid-001",
)

invalid_decision = create_decision_object(
    requestor="human-001",
    authority="Operations Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Deploy application through over-scoped subagent",
    evidence_references=["deployment-evidence-002"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "DEPLOYED"},
    governed_resource="service-B",
)

invalid_gov = create_governance_receipt(invalid_decision)

invalid_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Veridian",
    artifact_type="DECISION_OBJECT",
    artifact=invalid_decision.to_dict(),
    policy_version="policy-v1",
)

invalid_result = verify_intent(
    invalid_decision,
    invalid_gov,
    invalid_boundary,
    invalid_chain,
    invalid_child_evidence,
    invalid_authority_boundary,
    authority_state_evidence=invalid_state,
    authority_state_boundary_receipt=invalid_state_boundary,
    execution_time=execution_time,
    parent_authority_evidence=parent_authority_evidence,
    parent_authority_boundary_receipt=parent_authority_boundary,
)

print("EXPANDED CHILD DELEGATION:", invalid_result.to_dict())

assert invalid_result.status == "FAILED"
assert invalid_result.reason == "RESOURCE_AUTHORITY_EXPANSION"
assert invalid_result.intent_receipt_id is None

print(
    "PASS: subagent delegation remained bounded by parent authority"
)

# ------------------------------------------------------------------
# CASE 3: hash-valid parent evidence without trusted parent provenance
# ------------------------------------------------------------------

untrusted_parent_result = verify_intent(
    valid_decision,
    valid_gov,
    valid_boundary,
    valid_chain,
    valid_child_evidence,
    valid_authority_boundary,
    authority_state_evidence=valid_state,
    authority_state_boundary_receipt=valid_state_boundary,
    execution_time=execution_time,
    parent_authority_evidence=parent_authority_evidence,
    parent_authority_boundary_receipt=None,
)

print("UNTRUSTED PARENT DELEGATION:", untrusted_parent_result.to_dict())

assert untrusted_parent_result.status == "FAILED"
assert untrusted_parent_result.reason == "MISSING_PARENT_AUTHORITY_BOUNDARY"
assert untrusted_parent_result.intent_receipt_id is None

print(
    "PASS: hash-valid parent evidence without trusted provenance "
    "did not create inheritable authority"
)
