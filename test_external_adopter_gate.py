"""Local guarded-adopter regression. No real payments or network."""

import contextlib
import io
import runpy

from executor.guarded_execution import execute_with_current_authority
from mock_external_payment_service import MockExternalPaymentService

# Reuse the existing, previously tested authority fixture.
with contextlib.redirect_stdout(io.StringIO()):
    fixture = runpy.run_path("test_guarded_execution_revocation.py")

service = MockExternalPaymentService()
credential = "TEST-API-CREDENTIAL"

def guarded_payment(state, boundary, execution_time, *, scenario=None):
    source = fixture if scenario is None else scenario
    decision = source.get("payment", source.get("decision"))

    verification, receipt, record, execution = (
        execute_with_current_authority(
            decision,
            source["gov"],
            source["boundary"],
            source["responsibility_chain"],
            source["authority_evidence"],
            source["authority_boundary_receipt"],
            state,
            boundary,
            execution_time,
            source["trusted_key_registry"],
        )
    )

    # Fail closed. No external forwarding on any mismatch.
    permitted = (
        verification.status == "VERIFIED"
        and verification.verified_action == "EXECUTE_PAYMENT"
        and record.status == "VERIFIED"
        and record.verified_action == "EXECUTE_PAYMENT"
        and execution.status == "EXECUTED"
        and execution.action == "EXECUTE_PAYMENT"
        and decision.intended_action == "EXECUTE_PAYMENT"
        and decision.governed_resource is not None
        and decision.requested_authority_units is not None
        and decision.requested_authority_units > 0
    )

    if not permitted:
        return verification, execution

    service.execute_payment(
        credential,
        decision.governed_resource,
        decision.requested_authority_units,
        decision.decision_id,
    )

    return verification, execution


# Positive: active delegated authority.
verification, execution = guarded_payment(
    fixture["active_state"],
    fixture["active_state_boundary"],
    fixture["authorization_time"],
)

assert verification.status == "VERIFIED"
assert len(service.requests) == 1
assert len(service.completed) == 1
assert service.completed[0]["amount"] == 500
assert service.completed[0]["payee"] == "payee-A"
print("PASS: AUTHORIZED PAYMENT REACHED MOCK SERVICE ONCE")

# Negative: the same authority has subsequently been revoked.
verification, execution = guarded_payment(
    fixture["revoked_state"],
    fixture["revoked_state_boundary"],
    fixture["execution_time"],
)

assert verification.status == "FAILED"
assert verification.reason == "REVOKED_AUTHORITY"
assert execution.status == "FAILED_CLOSED"
assert len(service.requests) == 1
assert len(service.completed) == 1

print("PASS: REVOKED AUTHORITY BLOCKED ADDITIONAL REQUEST")
print("PASS: MOCK SERVICE RECORDED NO ADDITIONAL PAYMENT")
print("PASS: EXTERNAL ADOPTER ACTIVE/REVOKED REGRESSION")

# Negative: host has payment capability, but delegated authority
# permits production deployment only.
with contextlib.redirect_stdout(io.StringIO()):
    host_fixture = runpy.run_path(
        "test_unmonitored_execution_with_host_authority_escape.py"
    )

host_verification = host_fixture["verification"]
host_execution = host_fixture["execution"]

before_requests = len(service.requests)
before_completed = len(service.completed)

assert "EXECUTE_PAYMENT" in host_fixture["host_capabilities"]
assert host_verification.status == "FAILED"
assert host_verification.reason == "OUT_OF_SCOPE"
assert host_execution.status == "FAILED_CLOSED"
assert host_execution.action == "NONE"

# The guarded adapter must not forward this denied operation.
assert len(service.requests) == before_requests
assert len(service.completed) == before_completed

print("PASS: OUT-OF-SCOPE PAYMENT DENIED")
print("PASS: HOST CAPABILITY DID NOT CREATE PAYMENT AUTHORITY")
print("PASS: NO ADDITIONAL EXTERNAL PAYMENT REQUEST")

# Fresh external-adopter denial:
# The host can execute payments, but its authority permits deployment only.
from datetime import datetime, timezone

requests_before = len(service.requests)
completed_before = len(service.completed)

(
    fresh_host_verification,
    fresh_host_receipt,
    fresh_host_record,
    fresh_host_execution,
) = execute_with_current_authority(
    host_fixture["decision"],
    host_fixture["gov"],
    host_fixture["boundary"],
    host_fixture["responsibility_chain"],
    host_fixture["authority_evidence"],
    host_fixture["authority_boundary_receipt"],
    host_fixture["authority_state_evidence"],
    host_fixture["authority_state_boundary_receipt"],
    datetime.now(timezone.utc),
    host_fixture["trusted_key_registry"],
)

assert fresh_host_verification.status == "FAILED"
assert fresh_host_verification.reason == "OUT_OF_SCOPE"
assert fresh_host_verification.verified_action is None
assert fresh_host_receipt.verification_status == "FAILED"
assert fresh_host_record.status == "FAILED"
assert fresh_host_record.verified_action is None
assert fresh_host_execution.status == "FAILED_CLOSED"
assert fresh_host_execution.action == "NONE"

assert len(service.requests) == requests_before
assert len(service.completed) == completed_before

print("PASS: FRESH OUT-OF-SCOPE AUTHORITY DENIED")
print("PASS: FRESH DENIAL FAILED CLOSED")
print("PASS: ZERO ADDITIONAL MOCK SERVICE REQUESTS")

# Unified adapter: fresh out-of-scope request.
unified_before = len(service.requests)
unified_completed_before = len(service.completed)

unified_verification, unified_execution = guarded_payment(
    host_fixture["authority_state_evidence"],
    host_fixture["authority_state_boundary_receipt"],
    datetime.now(timezone.utc),
    scenario=host_fixture,
)

assert unified_verification.status == "FAILED"
assert unified_verification.reason == "OUT_OF_SCOPE"
assert unified_verification.verified_action is None
assert unified_execution.status == "FAILED_CLOSED"
assert unified_execution.action == "NONE"

assert len(service.requests) == unified_before
assert len(service.completed) == unified_completed_before

print("PASS: UNIFIED ADAPTER DENIED OUT-OF-SCOPE PAYMENT")
print("PASS: UNIFIED ADAPTER FORWARDED ZERO UNAUTHORIZED REQUESTS")
