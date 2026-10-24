from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from executor.executor import _execute_verified_intent
from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture


# The decision carries scientific evidence supporting the proposed experiment.
# That evidence must not itself manufacture authority to perform the experiment.
decision = create_decision_object(
    requestor="scientific-agent-001",
    authority="Research Review Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Run scientifically supported experiment",
    evidence_references=[
        "scientific-analysis-001",
        "mechanism-validation-001",
        "constraint-check-001",
    ],
    decision="APPROVED",
    intended_action="RUN_EXPERIMENT",
    intended_state={"experiment_status": "RUNNING"},
)

gov = create_governance_receipt(decision)

boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=decision.to_dict(),
    policy_version="policy-v1",
)


# CASE 1:
# The system has trusted authority, but only for Production Deployment.
# Scientific evidence must not expand that authority into experimental authority.
(
    deployment_chain,
    deployment_authority_evidence,
    deployment_authority_boundary_receipt,
    deployment_trusted_key_registry,
) = create_trusted_authority_fixture(
    authority_scope="Production Deployment",
    decision_authority="Research Review Committee",
)

(
    deployment_state_evidence,
    deployment_state_boundary_receipt,
) = create_authority_state_fixture(
    deployment_chain,
    deployment_authority_evidence,
    state="ACTIVE",
)

denied = verify_intent(
    decision,
    gov,
    boundary,
    deployment_chain,
    deployment_authority_evidence,
    deployment_authority_boundary_receipt,
    deployment_state_evidence,
    deployment_state_boundary_receipt,
    trusted_key_registry=deployment_trusted_key_registry,
)

print("SCIENTIFIC EVIDENCE WITHOUT EXPERIMENTAL AUTHORITY:", denied.to_dict())

denied_intent_receipt = create_intent_receipt(boundary, denied)
denied_intent_record = create_intent_record(
    gov,
    boundary,
    denied_intent_receipt,
)
denied_execution = _execute_verified_intent(denied_intent_record)

print("DENIED EXECUTION:", denied_execution.to_dict())

assert denied.status == "FAILED"
assert denied.reason == "OUT_OF_SCOPE"
assert denied.intent_receipt_id is None
assert denied.verified_action is None
assert denied_execution.status == "FAILED_CLOSED"
assert denied_execution.action == "NONE"


# CASE 2:
# The same scientific evidence becomes executable only when explicit
# Experimental Operations authority is actually delegated.
(
    experimental_chain,
    experimental_authority_evidence,
    experimental_authority_boundary_receipt,
    experimental_trusted_key_registry,
) = create_trusted_authority_fixture(
    authority_scope="Experimental Operations",
    decision_authority="Research Review Committee",
)

(
    experimental_state_evidence,
    experimental_state_boundary_receipt,
) = create_authority_state_fixture(
    experimental_chain,
    experimental_authority_evidence,
    state="ACTIVE",
)

verified = verify_intent(
    decision,
    gov,
    boundary,
    experimental_chain,
    experimental_authority_evidence,
    experimental_authority_boundary_receipt,
    experimental_state_evidence,
    experimental_state_boundary_receipt,
    trusted_key_registry=experimental_trusted_key_registry,
)

print("WITH EXPLICIT EXPERIMENTAL AUTHORITY:", verified.to_dict())

assert verified.status == "VERIFIED"
assert verified.intent_receipt_id is not None
assert verified.verified_action == "RUN_EXPERIMENT"

print(
    "PASS: scientific evidence did not create experimental authority; "
    "explicit delegation was required"
)
