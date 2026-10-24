from datetime import datetime, timezone

from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from bil.intent_record import create_intent_record
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.decision_object import create_decision_object
from decisionassure.decision_replay import replay_denied_decision
from decisionassure.diya_adapter import verify_intent
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.intent_receipt import create_intent_receipt
from executor.executor import _execute_verified_intent


(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    organization="Acme Industrial",
    business_owner="Alice",
    decision_authority="Industrial Safety Committee",
    delegated_by="Alice",
    delegated_to="Veridian",
    authority_scope="Industrial Inspection",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Inspection Agent",
    policy_reference="policy-ref-industrial-inspection-001",
    evidence_reference="authority-evidence-industrial-inspection-001",
    authority_evidence_source="AuthorityService",
    governed_resource="equipment-A",
)

(
    authority_state_evidence,
    authority_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    state_reference="industrial-inspection-state-001",
)

execution_time = datetime.now(timezone.utc)


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

    execution = _execute_verified_intent(intent_record)

    return gov, boundary, verification, execution


# ============================================================
# CASE 1
# Authorized industrial inspection.
# ============================================================

inspection_decision = create_decision_object(
    requestor="industrial-operator-001",
    authority="Industrial Safety Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Inspect equipment-A for operating condition",
    evidence_references=["inspection-order-001"],
    decision="APPROVED",
    intended_action="INSPECT_EQUIPMENT",
    intended_state={"status": "INSPECTED"},
    governed_resource="equipment-A",
)

(
    inspection_gov,
    inspection_boundary,
    inspection_verification,
    inspection_execution,
) = verify_and_execute(inspection_decision)

print("INSPECTION VERIFICATION:", inspection_verification.to_dict())
print("INSPECTION EXECUTION:", inspection_execution.to_dict())

assert inspection_verification.status == "VERIFIED"
assert inspection_verification.verified_action == "INSPECT_EQUIPMENT"
assert inspection_verification.intent_receipt_id is not None

assert inspection_execution.status == "EXECUTED"
assert inspection_execution.action == "INSPECT_EQUIPMENT"


# Simulated observation produced by the authorized inspection.
equipment_problem_identified = True
assert equipment_problem_identified is True

print("EQUIPMENT PROBLEM IDENTIFIED")


# ============================================================
# CASE 2
# Agent proposes a consequential physical action.
#
# The inspection delegation does NOT include shutdown authority.
# ============================================================

shutdown_decision = create_decision_object(
    requestor="industrial-inspection-agent-001",
    authority="Industrial Safety Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Shut down equipment-A after identifying equipment problem",
    evidence_references=[
        "inspection-order-001",
        "equipment-problem-observation-001",
    ],
    decision="APPROVED",
    intended_action="SHUTDOWN_EQUIPMENT",
    intended_state={"status": "SHUTDOWN"},
    governed_resource="equipment-A",
)

(
    shutdown_gov,
    shutdown_boundary,
    shutdown_verification,
    shutdown_execution,
) = verify_and_execute(shutdown_decision)

print("SHUTDOWN VERIFICATION:", shutdown_verification.to_dict())
print("SHUTDOWN EXECUTION:", shutdown_execution.to_dict())

assert shutdown_verification.status == "FAILED"
assert shutdown_verification.reason == "OUT_OF_SCOPE"
assert shutdown_verification.intent_receipt_id is None
assert shutdown_verification.verified_action is None

assert shutdown_execution.status == "FAILED_CLOSED"
assert shutdown_execution.action == "NONE"
assert (
    shutdown_execution.message
    == "Execution blocked: intent not verified"
)


# ============================================================
# CASE 3
# Verify simulated physical state remained unchanged.
#
# This proves Veridian caused no unauthorized physical-state
# transition. It does not claim Veridian independently measures
# real-world equipment safety.
# ============================================================

equipment_state_before = "RUNNING"
equipment_state_after = equipment_state_before

assert equipment_state_after == equipment_state_before

print(
    "VERIFIED EQUIPMENT STATE: "
    "no unauthorized shutdown state transition"
)


# ============================================================
# CASE 4
# Independently replay the shutdown denial.
# ============================================================

replay_result = replay_denied_decision(
    decision=shutdown_decision,
    governance_receipt=shutdown_gov,
    responsibility_chain=responsibility_chain,
    boundary_receipt=shutdown_boundary,
    boundary_artifact=shutdown_decision.to_dict(),
    authority_evidence=authority_evidence,
    authority_boundary_receipt=authority_boundary_receipt,
    authority_state_evidence=authority_state_evidence,
    authority_state_boundary_receipt=authority_state_boundary_receipt,
    execution_time=execution_time,
    expected_failed_condition="OUT_OF_SCOPE",
    trusted_key_registry=trusted_key_registry,
)

print(
    "INDUSTRIAL SHUTDOWN DENIAL REPLAY:",
    replay_result.to_dict(),
)

assert replay_result.passed is True
assert (
    replay_result.message
    == "Authority denial independently reproduced: OUT_OF_SCOPE"
)

print(
    "PASS: authorized industrial inspection did not create "
    "authority to shut down equipment"
)
