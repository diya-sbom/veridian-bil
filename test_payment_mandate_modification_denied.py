from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from bvp.boundary_receipt import create_boundary_receipt
from executor.executor import _execute_verified_intent
from authority_fixture import create_trusted_authority_fixture
from authority_state_fixture import create_authority_state_fixture
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bvp.trust_root import sign_payload


# Trusted, signed authority is explicitly limited to:
# - EXECUTE_PAYMENT
# - payee-A
# - 500 USD total authority
(
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    trusted_key_registry,
) = create_trusted_authority_fixture(
    decision_authority="Treasury Committee",
    authority_scope="Payment Operations",
    agent="Payment Agent",
    policy_reference="policy-ref-payment-001",
    evidence_reference="signed-payment-mandate-001",
    governed_resource="payee-A",
)

(
    authority_state_evidence,
    authority_state_boundary_receipt,
) = create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    aggregate_limit=500,
    consumed_units=0,
    authority_unit="USD",
    state_reference="payment-mandate-state-001",
)



# A trusted identity credential proves who the agent is.
# It does not grant or expand consequential authority.
identity_issuer = "AgentIdentityService"
identity_subject = "trusted-payment-agent-001"

identity_private_key = Ed25519PrivateKey.generate()
identity_key_id = trusted_key_registry.register(
    identity_issuer,
    identity_private_key.public_key(),
)

identity_payload = {
    "credential_type": "AGENT_IDENTITY",
    "issuer": identity_issuer,
    "subject": identity_subject,
}

identity_signature = sign_payload(
    identity_private_key,
    identity_payload,
)

identity_verified = trusted_key_registry.verify(
    identity_issuer,
    identity_key_id,
    identity_payload,
    identity_signature,
)

assert identity_verified is True
assert identity_payload["subject"] == "trusted-payment-agent-001"

print("TRUSTED AGENT IDENTITY: VERIFIED")

# A trusted reputation attestation may describe confidence in the agent,
# but reputation must never manufacture consequential authority.
reputation_issuer = "AgentReputationService"
reputation_private_key = Ed25519PrivateKey.generate()
reputation_key_id = trusted_key_registry.register(
    reputation_issuer,
    reputation_private_key.public_key(),
)

reputation_payload = {
    "attestation_type": "AGENT_REPUTATION",
    "issuer": reputation_issuer,
    "subject": identity_subject,
    "reputation_score": 0.99,
}

reputation_signature = sign_payload(
    reputation_private_key,
    reputation_payload,
)

reputation_verified = trusted_key_registry.verify(
    reputation_issuer,
    reputation_key_id,
    reputation_payload,
    reputation_signature,
)

assert reputation_verified is True
assert reputation_payload["reputation_score"] == 0.99

print("HIGH AGENT REPUTATION: VERIFIED")


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
        trusted_key_registry=trusted_key_registry,
    )

    intent_receipt = create_intent_receipt(boundary, verification)

    intent_record = create_intent_record(
        gov,
        boundary,
        intent_receipt,
    )

    execution = _execute_verified_intent(intent_record)

    return verification, execution


# CASE 1:
# Exact transaction permitted by the signed mandate.
authorized_payment = create_decision_object(
    requestor="trusted-payment-agent-001",
    authority="Treasury Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Execute authorized payment",
    evidence_references=["signed-payment-mandate-001"],
    decision="APPROVED",
    intended_action="EXECUTE_PAYMENT",
    intended_state={"status": "PAYMENT_REQUESTED"},
    requested_authority_units=500,
    requested_authority_unit="USD",
    governed_resource="payee-A",
)

authorized_verification, authorized_execution = verify_and_execute(
    authorized_payment
)

print("AUTHORIZED PAYMENT VERIFICATION:", authorized_verification.to_dict())
print("AUTHORIZED PAYMENT EXECUTION:", authorized_execution.to_dict())

assert authorized_verification.status == "VERIFIED"
assert authorized_verification.intent_receipt_id is not None
assert authorized_verification.verified_action == "EXECUTE_PAYMENT"
assert authorized_execution.status == "EXECUTED"
assert authorized_execution.action == "EXECUTE_PAYMENT"


# CASE 2:
# Same trusted agent, same valid mandate, same authorized payee,
# but the agent changes the transaction amount from 500 USD to 5,000 USD.
modified_payment = create_decision_object(
    requestor="trusted-payment-agent-001",
    authority="Treasury Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Execute modified payment",
    evidence_references=["signed-payment-mandate-001"],
    decision="APPROVED",
    intended_action="EXECUTE_PAYMENT",
    intended_state={"status": "PAYMENT_REQUESTED"},
    requested_authority_units=5000,
    requested_authority_unit="USD",
    governed_resource="payee-A",
)

modified_verification, modified_execution = verify_and_execute(
    modified_payment
)

print("MODIFIED PAYMENT VERIFICATION:", modified_verification.to_dict())
print("MODIFIED PAYMENT EXECUTION:", modified_execution.to_dict())

assert modified_verification.status == "FAILED"
assert modified_verification.reason == "CUMULATIVE_AUTHORITY_EXHAUSTED"
assert modified_verification.intent_receipt_id is None
assert modified_verification.verified_action is None

assert modified_execution.status == "FAILED_CLOSED"
assert modified_execution.action == "NONE"
assert modified_execution.message == "Execution blocked: intent not verified"

print(
    "PASS: valid identity, high reputation, and signed payment mandate did not authorize "
    "a transaction amount outside the mandate"
)
