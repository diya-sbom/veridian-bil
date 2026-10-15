from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from authority_fixture import create_trusted_authority_fixture
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from bvp.boundary_receipt import create_boundary_receipt
from executor.executor import execute_intent
from authority_state_fixture import create_authority_state_fixture


(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    organization="Acme Corp",
    business_owner="Alice",
    decision_authority="Finance Committee",
    delegated_by="Alice",
    delegated_to="Veridian",
    authority_scope="Capability Acquisition",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Economic Agent",
    policy_reference="policy-ref-capability-001",
    evidence_reference="authority-evidence-capability-001",
    authority_evidence_source="AuthorityService",
)

authority_state_evidence, authority_state_boundary_receipt = (
    create_authority_state_fixture(
        responsibility_chain,
        authority_evidence,
        state="ACTIVE",
        state_reference="capability-authority-state-001",
    )
)


# CASE 1: acquiring the capability is explicitly authorized.

acquire_decision = create_decision_object(
    requestor="human-001",
    authority="Finance Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Acquire payment capability",
    evidence_references=["capability-evidence-001"],
    decision="APPROVED",
    intended_action="ACQUIRE_PAYMENT_CAPABILITY",
    intended_state={"status": "AVAILABLE"},
)

acquire_gov = create_governance_receipt(acquire_decision)

acquire_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=acquire_decision.to_dict(),
    policy_version="policy-v1",
)

acquire_verification = verify_intent(
    acquire_decision,
    acquire_gov,
    acquire_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    trusted_key_registry=trusted_key_registry,
)

acquire_intent_receipt = create_intent_receipt(
    acquire_boundary,
    acquire_verification,
)

acquire_intent_record = create_intent_record(
    acquire_gov,
    acquire_boundary,
    acquire_intent_receipt,
)

acquire_execution = execute_intent(acquire_intent_record)

print("ACQUIRE VERIFICATION:", acquire_verification.to_dict())
print("ACQUIRE EXECUTION:", acquire_execution.to_dict())

assert acquire_verification.status == "VERIFIED"
assert acquire_verification.intent_receipt_id is not None
assert acquire_execution.status == "EXECUTED"
assert acquire_execution.action == "ACQUIRE_PAYMENT_CAPABILITY"


# CASE 2:
# capability exists, but EXECUTE_PAYMENT was never delegated.

payment_decision = create_decision_object(
    requestor="human-001",
    authority="Finance Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Use acquired payment capability",
    evidence_references=["capability-evidence-001"],
    decision="APPROVED",
    intended_action="EXECUTE_PAYMENT",
    intended_state={"status": "PAID"},
)

payment_gov = create_governance_receipt(payment_decision)

payment_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=payment_decision.to_dict(),
    policy_version="policy-v1",
)

payment_verification = verify_intent(
    payment_decision,
    payment_gov,
    payment_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    trusted_key_registry=trusted_key_registry,
)

payment_intent_receipt = create_intent_receipt(
    payment_boundary,
    payment_verification,
)

payment_intent_record = create_intent_record(
    payment_gov,
    payment_boundary,
    payment_intent_receipt,
)

payment_execution = execute_intent(payment_intent_record)

print("PAYMENT VERIFICATION:", payment_verification.to_dict())
print("PAYMENT EXECUTION:", payment_execution.to_dict())

assert payment_verification.status == "FAILED"
assert payment_verification.reason == "OUT_OF_SCOPE"
assert payment_verification.intent_receipt_id is None

assert payment_execution.status == "FAILED_CLOSED"
assert payment_execution.action == "NONE"
assert payment_execution.message == "Execution blocked: intent not verified"

print(
    "PASS: authority to acquire payment capability did not create "
    "authority to exercise that capability"
)
