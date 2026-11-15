"""Unified local payment enforcement proof. No real payments."""
import contextlib
import io
import runpy
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

with contextlib.redirect_stdout(io.StringIO()):
    t = runpy.run_path("test_protected_payment_issuer_integration.py")

f = t["fixture"]
decision = t["decision"]

def issue():
    return t["issue_payment_authorization"](
        decision, f["active_state"], f["active_state_boundary"]
    )

def redeem(db_path, authorization, state, boundary,
           payee="payee-A", amount=500):
    denied = "FAILED_CLOSED"
    try:
        if not isinstance(authorization, dict):
            return denied

        payload = authorization["payload"]
        if not isinstance(payload, dict):
            return denied

        if not t["registry"].verify(
            authorization["issuer"],
            authorization["key_id"],
            payload,
            authorization["signature"],
        ):
            return denied

        expires = datetime.fromisoformat(payload["expires_at"])
        if expires.tzinfo is None or datetime.now(timezone.utc) >= expires:
            return denied

        if not (
            payload.get("action") == "EXECUTE_PAYMENT"
            and payload.get("audience") == "MOCK-PAYMENT-SERVICE"
            and payload.get("decision_id") == decision.decision_id
            and payload.get("payee") == payee == decision.governed_resource
            and type(payload.get("amount")) is int
            and payload["amount"] == amount == decision.requested_authority_units
            and isinstance(payload.get("authorization_id"), str)
            and bool(payload["authorization_id"])
        ):
            return denied

        with sqlite3.connect(db_path, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")

            existing = db.execute(
                "SELECT 1 FROM payments WHERE authorization_id=?",
                (payload["authorization_id"],)
            ).fetchone()

            if existing:
                db.rollback()
                return denied

            verification, _, record, execution = (
                t["execute_with_current_authority"](
                    decision, f["gov"], f["boundary"],
                    f["responsibility_chain"],
                    f["authority_evidence"],
                    f["authority_boundary_receipt"],
                    state, boundary, f["authorization_time"],
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
                db.rollback()
                return denied

            # The mock payment effect and replay identity are one row.
            db.execute(
                """INSERT INTO payments
                   (authorization_id, decision_id, payee, amount)
                   VALUES (?, ?, ?, ?)""",
                (
                    payload["authorization_id"],
                    decision.decision_id, payee, amount,
                ),
            )
            db.commit()
            return "COMPLETED"
    except Exception:
        return denied

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

    valid = issue()
    assert valid is not None

    assert redeem(
        path, valid, f["active_state"], f["active_state_boundary"]
    ) == "COMPLETED"
    print("PASS: AUTHORIZED SIGNED PAYMENT COMMITTED")

    assert redeem(
        path, valid, f["active_state"], f["active_state_boundary"]
    ) == "FAILED_CLOSED"
    print("PASS: DURABLE PAYMENT REPLAY REJECTED")

    stale = issue()
    assert redeem(
        path, stale, f["revoked_state"], f["revoked_state_boundary"]
    ) == "FAILED_CLOSED"
    print("PASS: REVOKED AUTHORITY REJECTED")

    substitute = issue()
    assert redeem(
        path, substitute, f["active_state"],
        f["active_state_boundary"], payee="payee-B"
    ) == "FAILED_CLOSED"
    print("PASS: PAYEE SUBSTITUTION REJECTED")

    amount_change = issue()
    assert redeem(
        path, amount_change, f["active_state"],
        f["active_state_boundary"], amount=1000
    ) == "FAILED_CLOSED"
    print("PASS: AMOUNT SUBSTITUTION REJECTED")

    assert redeem(
        path, None, f["active_state"], f["active_state_boundary"]
    ) == "FAILED_CLOSED"
    print("PASS: MISSING AUTHORIZATION REJECTED")

    with sqlite3.connect(path) as db:
        payments = db.execute(
            "SELECT COUNT(*) FROM payments"
        ).fetchone()[0]

    assert payments == 1
    print("PASS: EXACTLY ONE DURABLE MOCK PAYMENT")

print("PASS: UNIFIED LOCAL PAYMENT COMMIT REGRESSION")
