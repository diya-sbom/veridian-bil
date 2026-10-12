from datetime import datetime, timezone
from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from executor.executor import execute_intent


# Existing valid delegated authority.
(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture()

# Current execution-time authority state:
# aggregate limit = 10,000 units
# 9,999 units already consumed
(
    authority_state_evidence,
    authority_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    aggregate_limit=10_000,
    consumed_units=9_999,
    authority_unit="MICRO_PURCHASE_UNIT",
    state_reference="authority-state-cumulative-001",
)

execution_time = datetime.now(timezone.utc)


# CASE 1:
# Exactly the remaining authority is still valid.
boundary_decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Execute final authorized micro-purchase",
    evidence_references=["evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "ACTIVE"},
    requested_authority_units=1,
    requested_authority_unit="MICRO_PURCHASE_UNIT",
)

boundary_gov = create_governance_receipt(boundary_decision)

boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=boundary_decision.to_dict(),
    policy_version="policy-v1",
)

boundary_verification = verify_intent(
    boundary_decision,
    boundary_gov,
    boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time=execution_time,
    trusted_key_registry=trusted_key_registry,
)

print("BOUNDARY VERIFICATION:", boundary_verification.to_dict())

assert boundary_verification.status == "VERIFIED"
assert boundary_verification.intent_receipt_id is not None


# CASE 2:
# Individually valid action, but cumulative delegated authority is exhausted.
exhausted_decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Attempt purchase beyond remaining aggregate authority",
    evidence_references=["evidence-001"],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={"status": "ACTIVE"},
    requested_authority_units=2,
    requested_authority_unit="MICRO_PURCHASE_UNIT",
)

exhausted_gov = create_governance_receipt(exhausted_decision)

exhausted_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=exhausted_decision.to_dict(),
    policy_version="policy-v1",
)

exhausted_verification = verify_intent(
    exhausted_decision,
    exhausted_gov,
    exhausted_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time=execution_time,
    trusted_key_registry=trusted_key_registry,
)

exhausted_intent_receipt = create_intent_receipt(
    exhausted_boundary,
    exhausted_verification,
)

exhausted_intent_record = create_intent_record(
    exhausted_gov,
    exhausted_boundary,
    exhausted_intent_receipt,
)

exhausted_execution = execute_intent(exhausted_intent_record)

print("EXHAUSTED VERIFICATION:", exhausted_verification.to_dict())
print("EXHAUSTED EXECUTION:", exhausted_execution.to_dict())

assert exhausted_verification.status == "FAILED"
assert exhausted_verification.reason == "CUMULATIVE_AUTHORITY_EXHAUSTED"
assert exhausted_verification.intent_receipt_id is None

assert exhausted_execution.status == "FAILED_CLOSED"
assert exhausted_execution.action == "NONE"
assert exhausted_execution.message == "Execution blocked: intent not verified"

print(
    "PASS: individually valid action denied after aggregate delegated authority exhausted"
)
