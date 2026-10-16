from datetime import datetime, timezone
from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from authority_fixture import create_trusted_authority_fixture
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from bvp.boundary_receipt import create_boundary_receipt
from executor.executor import execute_intent
from authority_state_fixture import create_authority_state_fixture


# --------------------------------------------------
# Delegated authority:
#
#     DEPLOY -> service-A
#
# The proof must show that the same valid DEPLOY action
# cannot silently migrate to service-B.
# --------------------------------------------------

(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    organization="Acme Corp",
    business_owner="Alice",
    decision_authority="Operations Committee",
    delegated_by="Alice",
    delegated_to="Veridian",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Deployment Agent",
    policy_reference="policy-ref-deploy-001",
    evidence_reference="authority-evidence-deploy-001",
    authority_evidence_source="AuthorityService",
    governed_resource="service-A",
)

authority_state_evidence, authority_state_boundary_receipt = (
    create_authority_state_fixture(
        responsibility_chain,
        authority_evidence,
        state="ACTIVE",
        state_reference="deploy-authority-state-001",
    )
)


# ==================================================
# CASE 1
# Exact authorized action on exact authorized resource.
# DEPLOY -> service-A
# ==================================================

authorized_decision = create_decision_object(
    requestor="human-001",
    authority="Operations Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Deploy application to authorized service",
    evidence_references=["deployment-evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "DEPLOYED"},
    governed_resource="service-A",
)

authorized_gov = create_governance_receipt(authorized_decision)

authorized_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=authorized_decision.to_dict(),
    policy_version="policy-v1",
)

authorized_verification = verify_intent(
    authorized_decision,
    authorized_gov,
    authorized_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    trusted_key_registry=trusted_key_registry,
)

authorized_intent_receipt = create_intent_receipt(
    authorized_boundary,
    authorized_verification,
)

authorized_intent_record = create_intent_record(
    authorized_gov,
    authorized_boundary,
    authorized_intent_receipt,
)

authorized_execution = execute_intent(authorized_intent_record)

print("AUTHORIZED VERIFICATION:", authorized_verification.to_dict())
print("AUTHORIZED EXECUTION:", authorized_execution.to_dict())

assert authorized_verification.status == "VERIFIED"
assert authorized_verification.intent_receipt_id is not None
assert authorized_execution.status == "EXECUTED"
assert authorized_execution.action == "DEPLOY"


# ==================================================
# CASE 2
# Same authorized action, same authority, same policy,
# but a different governed resource.
#
# DEPLOY -> service-B
#
# Must fail because authority for service-A does not
# become authority over service-B.
# ==================================================

wrong_resource_decision = create_decision_object(
    requestor="human-001",
    authority="Operations Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Deploy application to different service",
    evidence_references=["deployment-evidence-002"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "DEPLOYED"},
    governed_resource="service-B",
)

wrong_resource_gov = create_governance_receipt(wrong_resource_decision)

wrong_resource_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=wrong_resource_decision.to_dict(),
    policy_version="policy-v1",
)

execution_time = datetime.now(timezone.utc)

wrong_resource_verification = verify_intent(
    wrong_resource_decision,
    wrong_resource_gov,
    wrong_resource_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    trusted_key_registry=trusted_key_registry,
    execution_time=execution_time,
)

wrong_resource_intent_receipt = create_intent_receipt(
    wrong_resource_boundary,
    wrong_resource_verification,
)

wrong_resource_intent_record = create_intent_record(
    wrong_resource_gov,
    wrong_resource_boundary,
    wrong_resource_intent_receipt,
)

wrong_resource_execution = execute_intent(wrong_resource_intent_record)

print("WRONG RESOURCE VERIFICATION:", wrong_resource_verification.to_dict())
print("WRONG RESOURCE EXECUTION:", wrong_resource_execution.to_dict())

assert wrong_resource_verification.status == "FAILED"
assert wrong_resource_verification.reason == "RESOURCE_OUT_OF_SCOPE"
assert wrong_resource_verification.intent_receipt_id is None

assert wrong_resource_execution.status == "FAILED_CLOSED"
assert wrong_resource_execution.action == "NONE"
assert (
    wrong_resource_execution.message
    == "Execution blocked: intent not verified"
)

print(
    "PASS: authority for service-A did not authorize "
    "the same DEPLOY action on service-B"
)
