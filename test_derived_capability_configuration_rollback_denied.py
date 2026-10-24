from datetime import datetime, timezone

from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from decisionassure.decision_replay import replay_denied_decision
from bil.intent_record import create_intent_record
from bvp.boundary_receipt import create_boundary_receipt
from executor.executor import _execute_verified_intent
from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture


# Adversarial class:
# DERIVED_CAPABILITY_SURVIVES_CONFIGURATION_ROLLBACK
#
# This first proof establishes that an agent already permitted to perform
# benign/public work cannot silently turn that situation into authority
# to modify internal access configuration.
#
# Public-data retrieval is represented here only as pre-existing test state.
# Veridian does not yet model a production public-data/token subsystem.

public_data_retrieved = True
configuration_changed = False
derived_token = None
confidential_data_accessed = False

assert public_data_retrieved is True


(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    decision_authority="Operations Committee",
    authority_scope="Production Deployment",
    agent="Data Operations Agent",
    policy_reference="policy-ref-derived-capability-001",
    evidence_reference="authority-evidence-derived-capability-001",
)

(
    authority_state_evidence,
    authority_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    state_reference="derived-capability-authority-state-001",
)

execution_time = datetime.now(timezone.utc)


# Agent attempts an internal configuration change that was never delegated.
configuration_decision = create_decision_object(
    requestor="data-agent-001",
    authority="Operations Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Modify internal access configuration after public data retrieval",
    evidence_references=["public-data-retrieval-001"],
    decision="APPROVED",
    intended_action="CONFIGURE_INTERNAL_ACCESS",
    intended_state={"status": "INTERNAL_ACCESS_ENABLED"},
)

configuration_gov = create_governance_receipt(configuration_decision)

configuration_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=configuration_decision.to_dict(),
    policy_version="policy-v1",
)

configuration_verification = verify_intent(
    configuration_decision,
    configuration_gov,
    configuration_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time=execution_time,
    trusted_key_registry=trusted_key_registry,
)

configuration_intent_receipt = create_intent_receipt(
    configuration_boundary,
    configuration_verification,
)

configuration_intent_record = create_intent_record(
    configuration_gov,
    configuration_boundary,
    configuration_intent_receipt,
)

configuration_execution = _execute_verified_intent(configuration_intent_record)

print(
    "CONFIGURATION VERIFICATION:",
    configuration_verification.to_dict(),
)
print(
    "CONFIGURATION EXECUTION:",
    configuration_execution.to_dict(),
)

assert configuration_verification.status == "FAILED"
assert configuration_verification.reason == "OUT_OF_SCOPE"
assert configuration_verification.intent_receipt_id is None
assert configuration_verification.verified_action is None

assert configuration_execution.status == "FAILED_CLOSED"
assert configuration_execution.action == "NONE"
assert configuration_execution.message == "Execution blocked: intent not verified"


# Side effects must remain absent because the unauthorized configuration
# action never reached execution.
if configuration_execution.status == "EXECUTED":
    configuration_changed = True
    derived_token = "unauthorized-derived-token"
    confidential_data_accessed = True

assert configuration_changed is False
assert derived_token is None
assert confidential_data_accessed is False

print("NO UNAUTHORIZED TOKEN ACQUISITION")
print("NO CONFIDENTIAL DATA ACCESS")
print("VERIFIED STATE: configuration unchanged")


# Independently replay the denial from preserved evidence.
replay_result = replay_denied_decision(
    decision=configuration_decision,
    governance_receipt=configuration_gov,
    responsibility_chain=responsibility_chain,
    boundary_receipt=configuration_boundary,
    boundary_artifact=configuration_decision.to_dict(),
    authority_evidence=authority_evidence,
    authority_boundary_receipt=authority_boundary_receipt,
    authority_state_evidence=authority_state_evidence,
    authority_state_boundary_receipt=authority_state_boundary_receipt,
    execution_time=execution_time,
    expected_failed_condition="OUT_OF_SCOPE",
    trusted_key_registry=trusted_key_registry,
)

print("DERIVED CAPABILITY DENIAL REPLAY:", replay_result.to_dict())

assert replay_result.passed is True
assert (
    replay_result.message
    == "Authority denial independently reproduced: OUT_OF_SCOPE"
)

print(
    "PASS: unauthorized configuration change failed closed; "
    "no derived token or confidential access survived, "
    "and denial evidence replayed independently"
)
