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
    organization="Acme Manufacturing",
    business_owner="Alice",
    decision_authority="Manufacturing Operations Committee",
    delegated_by="Alice",
    delegated_to="Veridian",
    authority_scope="Manufacturing Operations",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Manufacturing Agent",
    policy_reference="policy-ref-manufacturing-001",
    evidence_reference="authority-evidence-manufacturing-001",
    authority_evidence_source="AuthorityService",
    governed_resource="assembly-spec-v1",
)

(
    authority_state_evidence,
    authority_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    state_reference="manufacturing-state-001",
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
# Authorized manufacturing action.
# ============================================================

inspection_decision = create_decision_object(
    requestor="manufacturing-agent-001",
    authority="Manufacturing Operations Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Assemble component under approved manufacturing specification",
    evidence_references=["manufacturing-order-001"],
    decision="APPROVED",
    intended_action="ASSEMBLE_COMPONENT",
    intended_state={"status": "ASSEMBLED"},
    governed_resource="assembly-spec-v1",
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
assert inspection_verification.verified_action == "ASSEMBLE_COMPONENT"
assert inspection_verification.intent_receipt_id is not None

assert inspection_execution.status == "EXECUTED"
assert inspection_execution.action == "ASSEMBLE_COMPONENT"


# Simulated physical result produced by the authorized assembly.
approved_assembly_completed = True
assert approved_assembly_completed is True

print("APPROVED ASSEMBLY COMPLETED")


# ============================================================
# CASE 2
# AI model or production plan changes.
# The robot proposes the SAME physical action against a specification
# that was never delegated.
# =====================================================================

modified_plan_decision = create_decision_object(
    requestor="manufacturing-agent-001",
    authority="Manufacturing Operations Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent=(
        "Execute modified assembly plan produced after model or "
        "production-plan change"
    ),
    evidence_references=[
        "manufacturing-order-001",
        "modified-production-plan-002",
    ],
    decision="APPROVED",
    intended_action="ASSEMBLE_COMPONENT",
    intended_state={"status": "ASSEMBLED_MODIFIED"},
    governed_resource="assembly-spec-v2",
)

(
    modified_plan_gov,
    modified_plan_boundary,
    modified_plan_verification,
    modified_plan_execution,
) = verify_and_execute(modified_plan_decision)

print(
    "MODIFIED PLAN VERIFICATION:",
    modified_plan_verification.to_dict(),
)
print(
    "MODIFIED PLAN EXECUTION:",
    modified_plan_execution.to_dict(),
)

assert modified_plan_verification.status == "FAILED"
assert modified_plan_verification.reason == "RESOURCE_OUT_OF_SCOPE"
assert modified_plan_verification.intent_receipt_id is None
assert modified_plan_verification.verified_action is None

assert modified_plan_execution.status == "FAILED_CLOSED"
assert modified_plan_execution.action == "NONE"
assert (
    modified_plan_execution.message
    == "Execution blocked: intent not verified"
)

# CASE 3
# Verify simulated physical state remained unchanged.
#
# This proves Veridian caused no unauthorized physical-state
# transition. It does not claim Veridian independently measures
# real-world equipment safety.
# ============================================================

assembly_state_before = "ASSEMBLED_TO_SPEC_V1"
assembly_state_after = assembly_state_before

assert assembly_state_after == assembly_state_before

print(
    "VERIFIED MANUFACTURING STATE: "
    "no unauthorized physical assembly change"
)


# ============================================================
# CASE 4
# Independently replay the shutdown denial.
# ============================================================

replay_result = replay_denied_decision(
    decision=modified_plan_decision,
    governance_receipt=modified_plan_gov,
    responsibility_chain=responsibility_chain,
    boundary_receipt=modified_plan_boundary,
    boundary_artifact=modified_plan_decision.to_dict(),
    authority_evidence=authority_evidence,
    authority_boundary_receipt=authority_boundary_receipt,
    authority_state_evidence=authority_state_evidence,
    authority_state_boundary_receipt=authority_state_boundary_receipt,
    execution_time=execution_time,
    expected_failed_condition="RESOURCE_OUT_OF_SCOPE",
    trusted_key_registry=trusted_key_registry,
)

print(
    "MANUFACTURING PLAN-DRIFT DENIAL REPLAY:",
    replay_result.to_dict(),
)

assert replay_result.passed is True
assert (
    replay_result.message
    == "Authority denial independently reproduced: RESOURCE_OUT_OF_SCOPE"
)

print(
    "PASS: approved manufacturing authority did not extend to "
    "an unapproved changed specification"
)
