"""Test-only service-controlled authority boundary."""
import contextlib
import io
import runpy
import sqlite3
import tempfile
from pathlib import Path

with contextlib.redirect_stdout(io.StringIO()):
    t = runpy.run_path("test_unified_payment_commit.py")

f = t["f"]

with tempfile.TemporaryDirectory() as folder:
    path = str(Path(folder) / "payments.sqlite")

    with sqlite3.connect(path) as db:
        db.execute("""
            CREATE TABLE payments (
                authorization_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                payee TEXT NOT NULL,
                amount INTEGER NOT NULL
            )
        """)

    # Authority is selected by the test service operator,
    # not by a field in the payment request.
    current = {
        "state": f["active_state"],
        "boundary": f["active_state_boundary"],
    }

    def execute(request):
        try:
            if not isinstance(request, dict):
                return "FAILED_CLOSED"

            if request.get("action") != "EXECUTE_PAYMENT":
                return "FAILED_CLOSED"

            # Ignore caller-supplied authority claims.
            return t["redeem"](
                path,
                request.get("authorization"),
                current["state"],
                current["boundary"],
                payee=request.get("payee"),
                amount=request.get("amount"),
            )
        except Exception:
            return "FAILED_CLOSED"

    def payment_count():
        with sqlite3.connect(path) as db:
            return db.execute(
                "SELECT COUNT(*) FROM payments"
            ).fetchone()[0]

    def request_for(authorization):
        return {
            "action": "EXECUTE_PAYMENT",
            "authorization": authorization,
            "payee": "payee-A",
            "amount": 500,
        }

    # Authorization issued while authority is ACTIVE.
    stale_authorization = t["issue"]()
    assert stale_authorization is not None

    # Service operator revokes authority before redemption.
    current["state"] = f["revoked_state"]
    current["boundary"] = f["revoked_state_boundary"]

    forged = request_for(stale_authorization)
    forged["authority_state"] = "ACTIVE"
    forged["authority_boundary"] = "CALLER-SUPPLIED"

    assert execute(forged) == "FAILED_CLOSED"
    assert payment_count() == 0
    print("PASS: CALLER-SUPPLIED ACTIVE STATE IGNORED")
    print("PASS: REVOKED AUTHORITY REJECTED")
    print("PASS: ZERO PAYMENTS AFTER REVOCATION")

    # Separate positive-path scenario controlled by operator.
    current["state"] = f["active_state"]
    current["boundary"] = f["active_state_boundary"]

    valid_authorization = t["issue"]()
    assert valid_authorization is not None

    valid = request_for(valid_authorization)
    assert execute(valid) == "COMPLETED"
    assert payment_count() == 1
    print("PASS: SERVICE-CONTROLLED ACTIVE AUTHORITY ACCEPTED")

    assert execute(valid) == "FAILED_CLOSED"
    assert payment_count() == 1
    print("PASS: DURABLE REPLAY REJECTED")

print("PASS: SERVICE-CONTROLLED AUTHORITY REGRESSION")
