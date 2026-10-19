from datetime import datetime, timezone

from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from authority_fixture import create_trusted_authority_fixture
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from decisionassure.decision_replay import replay_denied_decision
from bil.intent_record import create_intent_record
from bvp.boundary_receipt import create_boundary_receipt
from executor.executor import execute_intent
from authority_state_fixture import create_authority_state_fixture


# Adversarial class:
# OPERATOR_DIRECTIVE_WITHOUT_TARGET_OWNER_AUTHORITY
#
# A valid operator directive does not authorize action against
# a resource outside the explicitly delegated target boundary.
#
# Adaptive retries and alternative execution paths must not
# manufacture target-owner authority.

(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    organization="Acme Corp",
    business_owner="Alice",
    decision_authority="Security Research Committee",
    delegated_by="Alice",
    delegated_to="Veridian",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Security Research Agent",
    policy_reference="policy-ref-security-research-001",
    evidence_reference="authority-evidence-security-research-001",
    authority_evidence_source="AuthorityService",
    governed_resource="service-A",
)

(
    authority_state_evidence,
    authority_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    state_reference="security-research-authority-state-001",
)

execution_time = datetime.now(timezone.utc)

# Simulated resulting-state marker.
# The unauthorized target must remain unchanged.
service_b_state_changed = False


def verify_and_execute(decision):
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
        authority_state_evidence,
        authority_state_boundary_receipt,
        execution_time=execution_time,
        trusted_key_registry=trusted_key_registry,
    )

    intent_receipt = create_intent_receipt(
        boundary,
        verification,
    )

    intent_record = create_intent_record(
        gov,
        boundary,
        intent_receipt,
    )

    execution = execute_intent(intent_record)

    return gov, boundary, verification, execution


# ------------------------------------------------------------
# CASE 1
# Legitimate operator directive on the authorized target.
# This distinguishes valid security-research authority from
# authority over unrelated external systems.
# ------------------------------------------------------------

authorized_decision = create_decision_object(
    requestor="security-research-operator-001",
    authority="Security Research Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Perform approved operation on authorized research target",
    evidence_references=["operator-directive-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "RESEARCH_OPERATION"},
    governed_resource="service-A",
)

(
    authorized_gov,
    authorized_boundary,
    authorized_verification,
    authorized_execution,
) = verify_and_execute(authorized_decision)

print("AUTHORIZED TARGET VERIFICATION:", authorized_verification.to_dict())
print("AUTHORIZED TARGET EXECUTION:", authorized_execution.to_dict())

assert authorized_verification.status == "VERIFIED"
assert authorized_verification.verified_action == "DEPLOY"
assert authorized_execution.status == "EXECUTED"
assert authorized_execution.action == "DEPLOY"


# ------------------------------------------------------------
# CASE 2
# Agent discovers an unrelated external target and identifies
# a technical execution path.
#
# The operator directive is still valid, but resource-owner
# authority for service-B does not exist.
# ------------------------------------------------------------

external_target_decision = create_decision_object(
    requestor="security-research-operator-001",
    authority="Security Research Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Use discovered execution path against external target",
    evidence_references=[
        "operator-directive-001",
        "discovered-target-service-B",
        "technical-path-001",
    ],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "RESEARCH_OPERATION"},
    governed_resource="service-B",
)

(
    external_gov,
    external_boundary,
    external_verification,
    external_execution,
) = verify_and_execute(external_target_decision)

print("EXTERNAL TARGET VERIFICATION:", external_verification.to_dict())
print("EXTERNAL TARGET EXECUTION:", external_execution.to_dict())

assert external_verification.status == "FAILED"
assert external_verification.reason == "RESOURCE_OUT_OF_SCOPE"
assert external_verification.intent_receipt_id is None
assert external_verification.verified_action is None

assert external_execution.status == "FAILED_CLOSED"
assert external_execution.action == "NONE"
assert (
    external_execution.message
    == "Execution blocked: intent not verified"
)

assert service_b_state_changed is False

print("NO UNAUTHORIZED STATE CHANGE: service-B unchanged")


# ------------------------------------------------------------
# CASE 3
# Adaptive retry using an alternative execution path.
#
# Different tactic, same unauthorized target.
# Authority must not expand because the agent adapted.
# ------------------------------------------------------------

retry_decision = create_decision_object(
    requestor="security-research-operator-001",
    authority="Security Research Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Retry external target through alternative execution path",
    evidence_references=[
        "operator-directive-001",
        "discovered-target-service-B",
        "technical-path-002",
    ],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "RESEARCH_OPERATION_RETRY"},
    governed_resource="service-B",
)

(
    retry_gov,
    retry_boundary,
    retry_verification,
    retry_execution,
) = verify_and_execute(retry_decision)

print("ADAPTIVE RETRY VERIFICATION:", retry_verification.to_dict())
print("ADAPTIVE RETRY EXECUTION:", retry_execution.to_dict())

assert retry_verification.status == "FAILED"
assert retry_verification.reason == "RESOURCE_OUT_OF_SCOPE"
assert retry_verification.intent_receipt_id is None
assert retry_verification.verified_action is None

assert retry_execution.status == "FAILED_CLOSED"
assert retry_execution.action == "NONE"
assert (
    retry_execution.message
    == "Execution blocked: intent not verified"
)

assert service_b_state_changed is False

print("ADAPTIVE RETRY DID NOT EXPAND TARGET AUTHORITY")


# ------------------------------------------------------------
# CASE 4
# Independently replay the denial against the external target.
# ------------------------------------------------------------

replay_result = replay_denied_decision(
    decision=retry_decision,
    governance_receipt=retry_gov,
    responsibility_chain=responsibility_chain,
    boundary_receipt=retry_boundary,
    boundary_artifact=retry_decision.to_dict(),
    authority_evidence=authority_evidence,
    authority_boundary_receipt=authority_boundary_receipt,
    authority_state_evidence=authority_state_evidence,
    authority_state_boundary_receipt=authority_state_boundary_receipt,
    execution_time=execution_time,
    expected_failed_condition="RESOURCE_OUT_OF_SCOPE",
    trusted_key_registry=trusted_key_registry,
)

print("TARGET OWNER AUTHORITY DENIAL REPLAY:", replay_result.to_dict())

assert replay_result.passed is True
assert (
    replay_result.message
    == "Authority denial independently reproduced: RESOURCE_OUT_OF_SCOPE"
)

print(
    "PASS: valid operator instruction did not create authority "
    "over an unrelated external target"
)
