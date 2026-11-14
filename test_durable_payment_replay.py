"""Test-only persistent replay gate. No real payments."""
import contextlib
import io
import multiprocessing as mp
import runpy
import sqlite3
import tempfile
from pathlib import Path

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

request = {
    "payee": decision.governed_resource,
    "amount": decision.requested_authority_units,
    "decision_id": decision.decision_id,
    "authorization": authorization,
}


def worker(db_path, mode, item, output):
    service = t["MockProtectedPaymentService"](t["registry"])
    connection = None
    status = "FAILED_CLOSED"

    try:
        connection = sqlite3.connect(db_path, timeout=10)
        connection.execute("BEGIN IMMEDIATE")

        auth = item.get("authorization")
        auth_id = auth["payload"]["authorization_id"]

        existing = connection.execute(
            "SELECT 1 FROM completed_payments WHERE authorization_id = ?",
            (auth_id,),
        ).fetchone()

        if existing is not None:
            connection.rollback()
            output.put(("FAILED_CLOSED", "REPLAY"))
            return

        state = (
            f["active_state"] if mode == "ACTIVE"
            else f["revoked_state"] if mode == "REVOKED"
            else None
        )
        boundary = (
            f["active_state_boundary"] if mode == "ACTIVE"
            else f["revoked_state_boundary"] if mode == "REVOKED"
            else None
        )

        if state is None or boundary is None:
            connection.rollback()
            output.put(("FAILED_CLOSED", "NO_AUTHORITY"))
            return

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

        permitted = (
            verification.status == "VERIFIED"
            and verification.verified_action == "EXECUTE_PAYMENT"
            and record.status == "VERIFIED"
            and execution.status == "EXECUTED"
            and execution.action == "EXECUTE_PAYMENT"
            and item["payee"] == decision.governed_resource
            and item["amount"] == decision.requested_authority_units
            and item["decision_id"] == decision.decision_id
        )

        if not permitted:
            connection.rollback()
            output.put(("FAILED_CLOSED", "AUTHORITY"))
            return

        result = service.execute_payment(
            "TEST-API-CREDENTIAL",
            item["payee"],
            item["amount"],
            item["decision_id"],
            authorization=auth,
        )
        status = result["status"]

        if status != "COMPLETED":
            connection.rollback()
            output.put(("FAILED_CLOSED", "BACKEND"))
            return

        connection.execute(
            """INSERT INTO completed_payments
               (authorization_id, decision_id, payee, amount)
               VALUES (?, ?, ?, ?)""",
            (
                auth_id,
                item["decision_id"],
                item["payee"],
                item["amount"],
            ),
        )
        connection.commit()
        output.put(("COMPLETED", "RECORDED"))

    except Exception:
        if connection is not None:
            connection.rollback()
        output.put(("FAILED_CLOSED", "ERROR"))
    finally:
        if connection is not None:
            connection.close()


def run(db_path, mode, item):
    ctx = mp.get_context("fork")
    queue = ctx.Queue()
    process = ctx.Process(
        target=worker,
        args=(db_path, mode, item, queue),
    )
    process.start()

    try:
        result = queue.get(timeout=30)
    finally:
        process.join(timeout=10)
        if process.is_alive():
            process.terminate()
            process.join()

    assert process.exitcode == 0
    return result


with tempfile.TemporaryDirectory() as directory:
    db_path = str(Path(directory) / "payments.sqlite")

    with sqlite3.connect(db_path) as db:
        db.execute(
            """CREATE TABLE completed_payments (
                 authorization_id TEXT PRIMARY KEY,
                 decision_id TEXT NOT NULL,
                 payee TEXT NOT NULL,
                 amount INTEGER NOT NULL
               )"""
        )

    first = run(db_path, "ACTIVE", request)
    assert first == ("COMPLETED", "RECORDED")
    print("PASS: FIRST PAYMENT COMPLETED AND RECORDED")

    restarted = run(db_path, "ACTIVE", request)
    assert restarted == ("FAILED_CLOSED", "REPLAY")
    print("PASS: REPLAY REJECTED AFTER WORKER RESTART")

    with sqlite3.connect(db_path) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM completed_payments"
        ).fetchone()[0]

    assert count == 1
    print("PASS: ONLY ONE DURABLE PAYMENT RECORD")

    second_auth = t["issue_payment_authorization"](
        decision,
        f["active_state"],
        f["active_state_boundary"],
    )
    assert second_auth is not None

    second_request = dict(request)
    second_request["authorization"] = second_auth

    revoked = run(db_path, "REVOKED", second_request)
    assert revoked[0] == "FAILED_CLOSED"
    print("PASS: REVOKED AUTHORITY STILL REJECTED")

    with sqlite3.connect(db_path) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM completed_payments"
        ).fetchone()[0]

    assert count == 1
    print("PASS: ZERO ADDITIONAL PAYMENTS AFTER REVOCATION")

print("PASS: TEST-ONLY DURABLE REPLAY REGRESSION")
