"""Test-only independent payment enforcement. No real payments."""
import base64
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bvp.trust_root import sign_payload

worker_code = r'''
import base64
import contextlib
import io
import json
import os
import runpy
import sqlite3
import sys
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from bvp.trust_root import verify_payload_signature
from executor.guarded_execution import execute_with_current_authority

with contextlib.redirect_stdout(io.StringIO()):
    f = runpy.run_path("test_guarded_execution_revocation.py")

decision = f["payment"]
# Authority is read from the service database at redemption.

states = {
    "ACTIVE": ("active_state", "active_state_boundary"),
    "REVOKED": ("revoked_state", "revoked_state_boundary"),
}

try:
    trusted = Ed25519PublicKey.from_public_bytes(
        base64.b64decode(
            os.environ["VERIDIAN_TEST_TRUSTED_PUBLIC_KEY"],
            validate=True,
        )
    )
except Exception:
    trusted = None

database = os.environ["VERIDIAN_TEST_PAYMENT_DB"]

with sqlite3.connect(database) as db:
    db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            authorization_id TEXT PRIMARY KEY,
            decision_id TEXT NOT NULL,
            payee TEXT NOT NULL,
            amount INTEGER NOT NULL
        )
    """)

def redeem(request):
    denied = {"status": "FAILED_CLOSED"}

    if not isinstance(request, dict):
        return denied

    if trusted is None:
        return denied

    try:
        authorization = request["authorization"]
        payload = authorization["payload"]
        signature = authorization["signature"]

        if not isinstance(payload, dict):
            return denied

        if not verify_payload_signature(trusted, payload, signature):
            return denied

        expires = datetime.fromisoformat(payload["expires_at"])

        if expires.tzinfo is None:
            return denied

        if datetime.now(timezone.utc) >= expires:
            return denied

        if not (
            request.get("action") == "EXECUTE_PAYMENT"
            and payload.get("action") == "EXECUTE_PAYMENT"
            and payload.get("audience") == "MOCK-PAYMENT-SERVICE"
            and payload.get("decision_id") == decision.decision_id
            and request.get("payee") == payload.get("payee")
            and payload.get("payee") == decision.governed_resource
            and type(request.get("amount")) is int
            and type(payload.get("amount")) is int
            and request["amount"] == payload["amount"]
            and payload["amount"] == decision.requested_authority_units
            and isinstance(payload.get("authorization_id"), str)
            and bool(payload["authorization_id"])
        ):
            return denied


        with sqlite3.connect(database, timeout=10) as db:
            # Test-only signal emitted when SQLite traces the
            # worker's BEGIN IMMEDIATE statement.
            marker = os.environ.get("VERIDIAN_TEST_LOCK_MARKER")
            if marker:
                def trace_transaction(statement):
                    if statement.strip().upper() == "BEGIN IMMEDIATE":
                        with open(marker, "w") as signal:
                            signal.write("TRANSACTION_ATTEMPTED")
                db.set_trace_callback(trace_transaction)

            db.execute("BEGIN IMMEDIATE")

            # Test-only pause AFTER acquiring the payment lock.
            held = os.environ.get("VERIDIAN_TEST_PAYMENT_HELD")
            release = os.environ.get("VERIDIAN_TEST_PAYMENT_RELEASE")
            if held and release:
                import time
                with open(held, "w") as signal:
                    signal.write("PAYMENT_LOCK_ACQUIRED")

                deadline = time.monotonic() + 10
                while not os.path.exists(release):
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            "Payment transaction release timed out"
                        )
                    time.sleep(0.01)


            # Read operator-owned authority under the payment lock.
            current = db.execute(
                "SELECT state FROM authority WHERE delegation_id=?",
                ("payment-delegation-001",),
            ).fetchone()

            if current is None or current[0] not in states:
                db.rollback()
                return denied

            state_key, boundary_key = states[current[0]]

            existing = db.execute(
                "SELECT 1 FROM payments WHERE authorization_id=?",
                (payload["authorization_id"],)
            ).fetchone()

            if existing:
                db.rollback()
                return denied

            with contextlib.redirect_stdout(io.StringIO()):
                verification, _, record, execution = (
                    execute_with_current_authority(
                        decision,
                        f["gov"],
                        f["boundary"],
                        f["responsibility_chain"],
                        f["authority_evidence"],
                        f["authority_boundary_receipt"],
                        f[state_key],
                        f[boundary_key],
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
                db.rollback()
                return denied

            db.execute(
                """INSERT INTO payments
                   (authorization_id, decision_id, payee, amount)
                   VALUES (?, ?, ?, ?)""",
                (
                    payload["authorization_id"],
                    decision.decision_id,
                    payload["payee"],
                    payload["amount"],
                ),
            )
            db.commit()

        return {"status": "COMPLETED"}

    except Exception:
        return denied

# The service announces its own decision identity.
print(json.dumps({
    "decision_id": decision.decision_id,
    "payee": decision.governed_resource,
    "amount": decision.requested_authority_units,
}), flush=True)

for line in sys.stdin:
    try:
        response = redeem(json.loads(line))
    except Exception:
        response = {"status": "FAILED_CLOSED"}
    print(json.dumps(response), flush=True)
'''

private_key = Ed25519PrivateKey.generate()
public_bytes = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)

with tempfile.TemporaryDirectory() as folder:
    database = str(Path(folder) / "payments.sqlite")

    with sqlite3.connect(database) as db:
        db.execute("""
            CREATE TABLE authority (
                delegation_id TEXT PRIMARY KEY,
                state TEXT NOT NULL
                    CHECK (state IN ('ACTIVE', 'REVOKED')),
                version INTEGER NOT NULL
            )
        """)
        db.execute(
            "INSERT INTO authority VALUES (?, ?, ?)",
            ("payment-delegation-001", "ACTIVE", 1),
        )

    def set_authority(mode):
        assert mode in ("ACTIVE", "REVOKED")
        with sqlite3.connect(database, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """UPDATE authority
                   SET state=?, version=version+1
                   WHERE delegation_id=?""",
                (mode, "payment-delegation-001"),
            )

    def start_worker(mode, lock_marker=None, held=None, release=None):
        env = os.environ.copy()
        env["VERIDIAN_TEST_PAYMENT_DB"] = database
        env.pop("VERIDIAN_TEST_LOCK_MARKER", None)
        env.pop("VERIDIAN_TEST_PAYMENT_HELD", None)
        env.pop("VERIDIAN_TEST_PAYMENT_RELEASE", None)
        if held is not None:
            env["VERIDIAN_TEST_PAYMENT_HELD"] = str(held)
        if release is not None:
            env["VERIDIAN_TEST_PAYMENT_RELEASE"] = str(release)
        if lock_marker is not None:
            env["VERIDIAN_TEST_LOCK_MARKER"] = str(lock_marker)
        # Operator changes durable authority, not worker environment.
        set_authority(mode)
        env.pop("VERIDIAN_TEST_AUTHORITY_MODE", None)
        env["VERIDIAN_TEST_TRUSTED_PUBLIC_KEY"] = (
            base64.b64encode(public_bytes).decode("ascii")
        )

        process = subprocess.Popen(
            [sys.executable, "-u", "-c", worker_code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        identity = json.loads(process.stdout.readline())
        return process, identity

    def submit(process, request):
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        return json.loads(process.stdout.readline())["status"]

    def payment_request(identity):
        payload = {
            "authorization_id": str(uuid4()),
            "action": "EXECUTE_PAYMENT",
            "decision_id": identity["decision_id"],
            "payee": identity["payee"],
            "amount": identity["amount"],
            "audience": "MOCK-PAYMENT-SERVICE",
            "expires_at": (
                datetime.now(timezone.utc) + timedelta(minutes=2)
            ).isoformat(),
        }
        return {
            "action": "EXECUTE_PAYMENT",
            "payee": identity["payee"],
            "amount": identity["amount"],
            "authorization": {
                "payload": payload,
                "signature": sign_payload(private_key, payload),
            },
        }

    active, identity = start_worker("ACTIVE")
    try:
        valid = payment_request(identity)

        assert submit(active, valid) == "COMPLETED"
        print("PASS: SIGNED PAYMENT COMMITTED BY INDEPENDENT WORKER")

        assert submit(active, valid) == "FAILED_CLOSED"
        print("PASS: DURABLE REPLAY REJECTED")

        changed = dict(valid, amount=1000)
        assert submit(active, changed) == "FAILED_CLOSED"
        print("PASS: AMOUNT SUBSTITUTION REJECTED")

        unsigned = dict(valid, authorization=None)
        assert submit(active, unsigned) == "FAILED_CLOSED"
        print("PASS: MISSING AUTHORIZATION REJECTED")

        forged = dict(valid, authority_state="ACTIVE")
        assert submit(active, forged) == "FAILED_CLOSED"
        print("PASS: CALLER AUTHORITY CLAIM CANNOT REPLAY PAYMENT")

        # Issue while active, revoke before first redemption.
        pending = payment_request(identity)
        set_authority("REVOKED")
        assert submit(active, pending) == "FAILED_CLOSED"
        print("PASS: POST-ISSUANCE REVOCATION BLOCKED PAYMENT")
    finally:
        active.stdin.close()
        active.wait(timeout=10)

    revoked, identity = start_worker("REVOKED")
    try:
        stale = payment_request(identity)
        stale["authority_state"] = "ACTIVE"

        assert submit(revoked, stale) == "FAILED_CLOSED"
        print("PASS: REVOKED AUTHORITY REJECTED IN INDEPENDENT WORKER")
    finally:
        revoked.stdin.close()
        revoked.wait(timeout=10)

    with sqlite3.connect(database) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM payments"
        ).fetchone()[0]

    assert count == 1
    print("PASS: EXACTLY ONE DURABLE MOCK PAYMENT")


    # FULL-WORKER REVOCATION RACE
    # Operator holds the write lock and revokes authority.
    # A signed payment request competes for the same database.
    import threading

    lock_marker = Path(folder) / "payment-lock-attempt.signal"
    race_worker, race_identity = start_worker(
        "ACTIVE", lock_marker=lock_marker
    )
    try:
        pending_signed = payment_request(race_identity)
        outcome = {}
        started = threading.Event()

        def attempt_payment():
            started.set()
            try:
                outcome["status"] = submit(
                    race_worker, pending_signed
                )
            except Exception as exc:
                outcome["error"] = repr(exc)

        with sqlite3.connect(database, timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                """UPDATE authority
                   SET state='REVOKED', version=version+1
                   WHERE delegation_id=?""",
                ("payment-delegation-001",),
            )

            competing = threading.Thread(
                target=attempt_payment, daemon=True
            )
            competing.start()
            assert started.wait(5), "Payment thread did not start"

            # Wait for the actual worker's SQLite trace signal.
            # The operator still holds the write transaction.
            import time
            deadline = time.monotonic() + 10
            while not lock_marker.exists():
                if time.monotonic() >= deadline:
                    raise AssertionError(
                        "Worker never reached BEGIN IMMEDIATE"
                    )
                time.sleep(0.01)

            assert lock_marker.read_text() == "TRANSACTION_ATTEMPTED"
            print("PASS: WORKER REACHED SQLITE TRANSACTION ATTEMPT")

            # Payment cannot acquire the SQLite writer lock
            # until this revocation transaction commits.
            db.commit()

        competing.join(timeout=15)
        assert not competing.is_alive(), "Payment timed out"
        assert outcome == {"status": "FAILED_CLOSED"}, outcome

        with sqlite3.connect(database) as db:
            state = db.execute(
                "SELECT state FROM authority WHERE delegation_id=?",
                ("payment-delegation-001",),
            ).fetchone()[0]
            count = db.execute(
                "SELECT COUNT(*) FROM payments"
            ).fetchone()[0]

        assert state == "REVOKED"
        assert count == 1, count

        print("PASS: FULL-WORKER REVOCATION RACE")
        print("PASS: COMPETING SIGNED PAYMENT DENIED")
        print("PASS: NO ADDITIONAL PAYMENT AFTER REVOCATION")
    finally:
        race_worker.stdin.close()
        race_worker.wait(timeout=10)


    # PAYMENT-FIRST SIGNED RACE VERIFIED
    import threading
    import time

    held = Path(folder) / "payment-first-held.signal"
    release = Path(folder) / "payment-first-release.signal"
    revocation_attempt = Path(folder) / "revocation-attempt.signal"

    def wait_for_signal(path, timeout=7):
        deadline = time.monotonic() + timeout
        while not path.exists():
            assert time.monotonic() < deadline, (
                "Missing synchronization signal: " + str(path)
            )
            time.sleep(0.01)

    payment_worker, payment_identity = start_worker(
        "ACTIVE", held=held, release=release
    )

    outcomes = {}

    def submit_payment():
        try:
            outcomes["payment"] = submit(
                payment_worker, signed_request
            )
        except Exception as exc:
            outcomes["payment_error"] = repr(exc)

    def revoke_authority():
        try:
            with sqlite3.connect(database, timeout=10) as db:
                def trace(statement):
                    if statement.strip().upper() == "BEGIN IMMEDIATE":
                        revocation_attempt.write_text(
                            "REVOCATION_TRANSACTION_ATTEMPTED"
                        )

                db.set_trace_callback(trace)
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    """UPDATE authority
                       SET state='REVOKED', version=version+1
                       WHERE delegation_id=?""",
                    ("payment-delegation-001",),
                )
                db.commit()
            outcomes["revocation"] = "COMMITTED"
        except Exception as exc:
            outcomes["revocation_error"] = repr(exc)

    payment_thread = None
    revocation_thread = None

    try:
        signed_request = payment_request(payment_identity)

        payment_thread = threading.Thread(target=submit_payment)
        payment_thread.start()

        # Worker must own the SQLite write lock.
        wait_for_signal(held)
        assert held.read_text() == "PAYMENT_LOCK_ACQUIRED"
        print("PASS: PAYMENT WORKER ACQUIRED WRITE LOCK")

        # Revocation now competes for the worker-held lock.
        revocation_thread = threading.Thread(target=revoke_authority)
        revocation_thread.start()

        wait_for_signal(revocation_attempt)
        assert revocation_attempt.read_text() == (
            "REVOCATION_TRANSACTION_ATTEMPTED"
        )
        assert "revocation" not in outcomes
        print("PASS: REVOCATION ATTEMPTED DURING PAYMENT")

        # Allow the authorized payment to commit first.
        release.touch()

        payment_thread.join(timeout=12)
        revocation_thread.join(timeout=12)

        assert not payment_thread.is_alive()
        assert not revocation_thread.is_alive()
        assert outcomes == {
            "payment": "COMPLETED",
            "revocation": "COMMITTED",
        }, outcomes

        with sqlite3.connect(database) as db:
            state = db.execute(
                "SELECT state FROM authority WHERE delegation_id=?",
                ("payment-delegation-001",),
            ).fetchone()[0]

            count = db.execute(
                "SELECT COUNT(*) FROM payments"
            ).fetchone()[0]

        assert state == "REVOKED", state
        assert count == 2, count
        print("PASS: SIGNED PAYMENT COMMITTED BEFORE REVOCATION")

        assert submit(payment_worker, signed_request) == "FAILED_CLOSED"
        print("PASS: PAYMENT REPLAY REJECTED")

        fresh = payment_request(payment_identity)
        assert submit(payment_worker, fresh) == "FAILED_CLOSED"

        with sqlite3.connect(database) as db:
            final_count = db.execute(
                "SELECT COUNT(*) FROM payments"
            ).fetchone()[0]

        assert final_count == 2, final_count
        print("PASS: FURTHER PAYMENTS DENIED AFTER REVOCATION")
        print("PASS: PAYMENT-FIRST SIGNED RACE VERIFIED")

    finally:
        release.touch()

        if payment_thread is not None:
            payment_thread.join(timeout=12)
        if revocation_thread is not None:
            revocation_thread.join(timeout=12)

        payment_worker.stdin.close()
        payment_worker.wait(timeout=10)

print("PASS: INDEPENDENT PAYMENT ENFORCEMENT REGRESSION")
