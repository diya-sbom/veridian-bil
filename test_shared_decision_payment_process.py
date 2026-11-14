"""Test-only forked payment worker; no real payments."""
import contextlib
import io
import multiprocessing as mp
import runpy

with contextlib.redirect_stdout(io.StringIO()):
    t = runpy.run_path("test_protected_payment_issuer_integration.py")

f = t["fixture"]
decision = t["decision"]

authorization = t["issue_payment_authorization"](
    decision,
    f["active_state"],
    f["active_state_boundary"],
)
assert authorization is not None

assert t["registry"].verify(
    authorization["issuer"],
    authorization["key_id"],
    authorization["payload"],
    authorization["signature"],
)

request = {
    "action": "EXECUTE_PAYMENT",
    "payee": decision.governed_resource,
    "amount": decision.requested_authority_units,
    "decision_id": decision.decision_id,
    "authorization": authorization,
}


def worker(mode, requests, output):
    # Backend exists only inside the worker for this test.
    service = t["MockProtectedPaymentService"](t["registry"])

    states = {
        "ACTIVE": (
            f["active_state"],
            f["active_state_boundary"],
        ),
        "REVOKED": (
            f["revoked_state"],
            f["revoked_state_boundary"],
        ),
    }
    selected = states.get(mode)

    for item in requests:
        status = "FAILED_CLOSED"
        try:
            if (
                selected is not None
                and item.get("action") == "EXECUTE_PAYMENT"
                and item.get("payee") == decision.governed_resource
                and item.get("amount") == decision.requested_authority_units
                and item.get("decision_id") == decision.decision_id
            ):
                verification, _, record, execution = (
                    t["execute_with_current_authority"](
                        decision,
                        f["gov"],
                        f["boundary"],
                        f["responsibility_chain"],
                        f["authority_evidence"],
                        f["authority_boundary_receipt"],
                        selected[0],
                        selected[1],
                        f["authorization_time"],
                        f["trusted_key_registry"],
                    )
                )

                if (
                    verification.status == "VERIFIED"
                    and verification.verified_action == "EXECUTE_PAYMENT"
                    and record.status == "VERIFIED"
                    and record.verified_action == "EXECUTE_PAYMENT"
                    and execution.status == "EXECUTED"
                    and execution.action == "EXECUTE_PAYMENT"
                ):
                    result = service.execute_payment(
                        "TEST-API-CREDENTIAL",
                        item["payee"],
                        item["amount"],
                        item["decision_id"],
                        authorization=item.get("authorization"),
                    )
                    status = result["status"]
        except Exception:
            status = "FAILED_CLOSED"

        output.put((status, len(service.completed)))


def run(mode, requests):
    ctx = mp.get_context("fork")
    output = ctx.Queue()
    process = ctx.Process(
        target=worker,
        args=(mode, requests, output),
    )
    process.start()
    results = []

    try:
        for _ in requests:
            results.append(output.get(timeout=30))
    finally:
        process.join(timeout=10)
        if process.is_alive():
            process.terminate()
            process.join()

    assert process.exitcode == 0
    return results


active = run("ACTIVE", [request, request])
assert active == [
    ("COMPLETED", 1),
    ("FAILED_CLOSED", 1),
]
print("PASS: SHARED DECISION ACCEPTED ACROSS PROCESSES")
print("PASS: REPLAY REJECTED")

revoked = run("REVOKED", [request])
assert revoked == [("FAILED_CLOSED", 0)]
print("PASS: REVOKED AUTHORITY REJECTED")
print("PASS: ZERO PAYMENTS AFTER REVOCATION")

forged = dict(request)
forged["authority_state"] = "ACTIVE"
assert run("REVOKED", [forged]) == [("FAILED_CLOSED", 0)]
print("PASS: CALLER-SUPPLIED AUTHORITY IGNORED")

missing = dict(request)
missing.pop("authorization")
assert run("ACTIVE", [missing]) == [("FAILED_CLOSED", 0)]
print("PASS: MISSING AUTHORIZATION REJECTED")

assert run("UNAVAILABLE", [request]) == [("FAILED_CLOSED", 0)]
print("PASS: UNAVAILABLE AUTHORITY FAILS CLOSED")

print("PASS: SHARED-DECISION PAYMENT PROCESS REGRESSION")
