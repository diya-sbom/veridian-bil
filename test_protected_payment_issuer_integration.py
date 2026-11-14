"""Local-only Veridian payment authorization integration proof."""

import contextlib
import io
import runpy
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.trust_root import TrustedKeyRegistry, sign_payload
from executor.guarded_execution import execute_with_current_authority
from mock_protected_payment_service import MockProtectedPaymentService


with contextlib.redirect_stdout(io.StringIO()):
    fixture = runpy.run_path("test_guarded_execution_revocation.py")

decision = fixture["payment"]
registry = TrustedKeyRegistry()
private_key = Ed25519PrivateKey.generate()
issuer = "VERIDIAN-TEST-ISSUER"
key_id = registry.register(issuer, private_key.public_key())
service = MockProtectedPaymentService(registry)


def issue_payment_authorization(decision, state, state_boundary):
    verification, receipt, record, execution = execute_with_current_authority(
        decision,
        fixture["gov"],
        fixture["boundary"],
        fixture["responsibility_chain"],
        fixture["authority_evidence"],
        fixture["authority_boundary_receipt"],
        state,
        state_boundary,
        fixture["authorization_time"],
        fixture["trusted_key_registry"],
    )

    permitted = (
        verification.status == "VERIFIED"
        and verification.verified_action == "EXECUTE_PAYMENT"
        and record.status == "VERIFIED"
        and record.verified_action == "EXECUTE_PAYMENT"
        and execution.status == "EXECUTED"
        and execution.action == "EXECUTE_PAYMENT"
        and decision.intended_action == "EXECUTE_PAYMENT"
        and isinstance(decision.governed_resource, str)
        and bool(decision.governed_resource)
        and type(decision.requested_authority_units) is int
        and decision.requested_authority_units > 0
    )

    if not permitted:
        return None

    payload = {
        "authorization_id": str(uuid4()),
        "action": "EXECUTE_PAYMENT",
        "payee": decision.governed_resource,
        "amount": decision.requested_authority_units,
        "decision_id": decision.decision_id,
        "audience": "MOCK-PAYMENT-SERVICE",
        "expires_at": (
            datetime.now(timezone.utc) + timedelta(minutes=2)
        ).isoformat(),
    }

    return {
        "issuer": issuer,
        "key_id": key_id,
        "signature": sign_payload(private_key, payload),
        "payload": payload,
    }


authorization = issue_payment_authorization(
    decision,
    fixture["active_state"],
    fixture["active_state_boundary"],
)

assert authorization is not None
print("PASS: GUARDED AUTHORITY CHECK ALLOWED ISSUANCE")

args = (
    "TEST-API-CREDENTIAL",
    decision.governed_resource,
    decision.requested_authority_units,
    decision.decision_id,
)

result = service.execute_payment(*args, authorization=authorization)
assert result["status"] == "COMPLETED"
assert len(service.completed) == 1
print("PASS: SIGNED AUTHORIZED PAYMENT COMPLETED")

replay = service.execute_payment(*args, authorization=authorization)
assert replay["status"] == "FAILED_CLOSED"
assert len(service.completed) == 1
print("PASS: AUTHORIZATION REPLAY REJECTED")

credential_only = service.execute_payment(*args)
assert credential_only["status"] == "FAILED_CLOSED"
assert len(service.completed) == 1
print("PASS: CREDENTIAL-ONLY PAYMENT REJECTED")

changed_payee = service.execute_payment(
    args[0], "payee-B", args[2], args[3],
    authorization=authorization,
)
assert changed_payee["status"] == "FAILED_CLOSED"
assert len(service.completed) == 1
print("PASS: PAYMENT DESTINATION SUBSTITUTION REJECTED")

print("PASS: INITIAL PROTECTED PAYMENT INTEGRATION")
