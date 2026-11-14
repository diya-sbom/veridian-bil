"""Test-only composition gateway; no real payments."""
import contextlib
import io
import runpy

with contextlib.redirect_stdout(io.StringIO()):
    t = runpy.run_path("test_payment_redemption_freshness.py")

fixture = t["f"]
integration = t["t"]
decision = integration["decision"]

current = {
    "state": fixture["active_state"],
    "boundary": fixture["active_state_boundary"],
}

class PaymentGateway:
    def __init__(self, registry):
        self._backend = integration["MockProtectedPaymentService"](registry)

    def execute_payment(self, credential, payee, amount, decision_id, authorization=None):
        try:
            if (
                payee != decision.governed_resource
                or amount != decision.requested_authority_units
                or decision_id != decision.decision_id
            ):
                return {"status": "FAILED_CLOSED"}

            verification, _, record, execution = integration[
                "execute_with_current_authority"
            ](
                decision,
                fixture["gov"],
                fixture["boundary"],
                fixture["responsibility_chain"],
                fixture["authority_evidence"],
                fixture["authority_boundary_receipt"],
                current["state"],
                current["boundary"],
                fixture["authorization_time"],
                fixture["trusted_key_registry"],
            )

            if not (
                verification.status == "VERIFIED"
                and verification.verified_action == "EXECUTE_PAYMENT"
                and record.status == "VERIFIED"
                and record.verified_action == "EXECUTE_PAYMENT"
                and execution.status == "EXECUTED"
                and execution.action == "EXECUTE_PAYMENT"
            ):
                return {"status": "FAILED_CLOSED"}
        except Exception:
            return {"status": "FAILED_CLOSED"}

        return self._backend.execute_payment(
            credential, payee, amount, decision_id,
            authorization=authorization,
        )

    @property
    def completed_count(self):
        return len(self._backend.completed)


gateway = PaymentGateway(integration["registry"])

authorization = integration["issue_payment_authorization"](
    decision, current["state"], current["boundary"]
)
assert authorization is not None

args = (
    "TEST-API-CREDENTIAL",
    decision.governed_resource,
    decision.requested_authority_units,
    decision.decision_id,
)

# Composition removes the inherited base-method path.
assert not isinstance(
    gateway, integration["MockProtectedPaymentService"]
)
print("PASS: GATEWAY DOES NOT INHERIT PAYMENT BACKEND")

# Revoke after issuance.
current["state"] = fixture["revoked_state"]
current["boundary"] = fixture["revoked_state_boundary"]

result = gateway.execute_payment(*args, authorization=authorization)
assert result["status"] == "FAILED_CLOSED"
assert gateway.completed_count == 0
print("PASS: REVOKED AUTHORITY REJECTED")
print("PASS: ZERO PAYMENTS AFTER REVOCATION")

# Restore valid authority.
current["state"] = fixture["active_state"]
current["boundary"] = fixture["active_state_boundary"]

result = gateway.execute_payment(*args, authorization=authorization)
assert result["status"] == "COMPLETED"
assert gateway.completed_count == 1
print("PASS: AUTHORIZED PAYMENT COMPLETED")

result = gateway.execute_payment(*args, authorization=authorization)
assert result["status"] == "FAILED_CLOSED"
assert gateway.completed_count == 1
print("PASS: REPLAY REJECTED")

print("PASS: TEST-ONLY COMPOSITION GATEWAY")
