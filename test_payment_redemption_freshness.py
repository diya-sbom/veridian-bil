"""Test-only payment redemption freshness proof. No real payments."""
import contextlib
import io
import runpy

with contextlib.redirect_stdout(io.StringIO()):
    t = runpy.run_path("test_protected_payment_issuer_integration.py")
    f = runpy.run_path("test_guarded_execution_revocation.py")

decision = t["decision"]
current = {
    "state": f["active_state"],
    "boundary": f["active_state_boundary"],
}

# This callback represents a service-controlled authority source.
# In production it must be independently authenticated and inaccessible
# for modification by the requesting agent.
def current_authority():
    return current["state"], current["boundary"]


class FreshnessEnforcedPaymentService(t["MockProtectedPaymentService"]):
    def __init__(self, registry, authority_source):
        super().__init__(registry)
        self._authority_source = authority_source

    def execute_payment(
        self, credential, payee, amount, decision_id, authorization=None
    ):
        if (
            payee != decision.governed_resource
            or amount != decision.requested_authority_units
            or decision_id != decision.decision_id
        ):
            return {"status": "FAILED_CLOSED"}

        try:
            state, boundary = self._authority_source()
            verification, _, record, execution = (
                t["execute_with_current_authority"](
                    decision,
                    f["gov"],
                    f["boundary"],
                    f["responsibility_chain"],
                    f["authority_evidence"],
                    f["authority_boundary_receipt"],
                    state,
                    boundary,
                    f["authorization_time"],
                    f["trusted_key_registry"],
                )
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

        return super().execute_payment(
            credential, payee, amount, decision_id,
            authorization=authorization,
        )


service = FreshnessEnforcedPaymentService(
    t["registry"], current_authority
)

authorization = t["issue_payment_authorization"](
    decision, current["state"], current["boundary"]
)
assert authorization is not None

args = (
    "TEST-API-CREDENTIAL",
    decision.governed_resource,
    decision.requested_authority_units,
    decision.decision_id,
)

# Revocation happens after token issuance but before redemption.
current["state"] = f["revoked_state"]
current["boundary"] = f["revoked_state_boundary"]

result = service.execute_payment(
    *args, authorization=authorization
)
assert result["status"] == "FAILED_CLOSED"
assert len(service.completed) == 0
assert len(service.requests) == 0
print("PASS: STALE AUTHORIZATION REJECTED AFTER REVOCATION")
print("PASS: ZERO EXTERNAL PAYMENTS AFTER REVOCATION")

# Restore authority for a separate positive-path demonstration.
current["state"] = f["active_state"]
current["boundary"] = f["active_state_boundary"]

result = service.execute_payment(
    *args, authorization=authorization
)
assert result["status"] == "COMPLETED"
assert len(service.completed) == 1
print("PASS: CURRENT AUTHORITY ALLOWS SIGNED PAYMENT")

result = service.execute_payment(
    *args, authorization=authorization
)
assert result["status"] == "FAILED_CLOSED"
assert len(service.completed) == 1
print("PASS: REPLAY STILL REJECTED")

print("PASS: TEST-ONLY REDEMPTION FRESHNESS GATE")
