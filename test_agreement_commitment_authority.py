from authority_state_fixture import create_authority_state_fixture
from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from authority_fixture import create_trusted_authority_fixture
from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from executor.executor import execute_intent


# Dedicated authority for operating an agreement system.
# This authority permits drafting/routing, but not creating
# a binding business commitment.
(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    organization="Acme Corp",
    business_owner="Alice",
    decision_authority="Legal Committee",
    delegated_by="Alice",
    delegated_to="Veridian",
    authority_scope="Agreement Operations",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Agreement Agent",
    policy_reference="policy-ref-agreement-001",
    evidence_reference="authority-evidence-agreement-001",
    authority_evidence_source="AuthorityService",
)


# ------------------------------------------------------------
authority_state_evidence, authority_state_boundary_receipt = (
    create_authority_state_fixture(
        responsibility_chain,
        authority_evidence,
        state="ACTIVE",
        state_reference="agreement-authority-state-001",
    )
)

# CASE 1:
# Permission to operate the agreement system.
# DRAFT_AGREEMENT is explicitly inside delegated scope.
# ------------------------------------------------------------
draft_decision = create_decision_object(
    requestor="human-001",
    authority="Legal Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Prepare vendor agreement",
    evidence_references=["agreement-evidence-001"],
    decision="APPROVED",
    intended_action="DRAFT_AGREEMENT",
    intended_state={"status": "DRAFT"},
)

draft_gov = create_governance_receipt(draft_decision)

draft_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=draft_decision.to_dict(),
    policy_version="policy-v1",
)

draft_verification = verify_intent(
    draft_decision,
    draft_gov,
    draft_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    trusted_key_registry=trusted_key_registry,
)

print("DRAFT:", draft_verification.to_dict())

assert draft_verification.status == "VERIFIED"
assert draft_verification.intent_receipt_id is not None


# ------------------------------------------------------------
# CASE 2:
# Same valid agreement-system authority attempts to create
# a binding business commitment.
#
# Capability / permission to operate the system must NOT
# expand into authority to bind the business.
# ------------------------------------------------------------
commitment_decision = create_decision_object(
    requestor="human-001",
    authority="Legal Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Create binding vendor commitment",
    evidence_references=["agreement-evidence-001"],
    decision="APPROVED",
    intended_action="CREATE_BUSINESS_COMMITMENT",
    intended_state={"status": "BOUND"},
)

commitment_gov = create_governance_receipt(commitment_decision)

commitment_boundary = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=commitment_decision.to_dict(),
    policy_version="policy-v1",
)

commitment_verification = verify_intent(
    commitment_decision,
    commitment_gov,
    commitment_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    trusted_key_registry=trusted_key_registry,
)

commitment_intent_receipt = create_intent_receipt(
    commitment_boundary,
    commitment_verification,
)

commitment_intent_record = create_intent_record(
    commitment_gov,
    commitment_boundary,
    commitment_intent_receipt,
)

commitment_execution = execute_intent(commitment_intent_record)

print("COMMITMENT:", commitment_verification.to_dict())
print("EXECUTION:", commitment_execution.to_dict())

assert commitment_verification.status == "FAILED"
assert commitment_verification.reason == "OUT_OF_SCOPE"
assert commitment_verification.intent_receipt_id is None

assert commitment_execution.status == "FAILED_CLOSED"
assert commitment_execution.action == "NONE"
assert commitment_execution.message == "Execution blocked: intent not verified"

print(
    "PASS: permission to operate agreement system "
    "does not create authority to make a business commitment"
)
