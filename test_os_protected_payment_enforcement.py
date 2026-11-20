admin_worker_code = '\nimport base64\nimport json\nimport os\nimport sqlite3\nimport sys\n\nfrom cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey\nfrom bvp.trust_root import verify_payload_signature\n\nkey = Ed25519PublicKey.from_public_bytes(\n    base64.b64decode(os.environ["VERIDIAN_TEST_OPERATOR_PUBLIC_KEY"])\n)\n\ndb = sqlite3.connect(os.environ["VERIDIAN_TEST_AUTHORITY_DB"], isolation_level=None)\ndb.execute("CREATE TABLE IF NOT EXISTS commands (command_id TEXT PRIMARY KEY)")\n\ndef current():\n    return db.execute(\n        "SELECT state, version FROM authority WHERE delegation_id=\'payment-delegation-001\'"\n    ).fetchone()\n\ndef apply(request):\n    denied = {"status": "FAILED_CLOSED"}\n    try:\n        auth = request["authorization"]\n        payload = auth["payload"]\n\n        if not isinstance(payload, dict):\n            return denied\n\n        if (\n            auth["issuer"] != "TEST-OPERATOR"\n            or not verify_payload_signature(key, payload, auth["signature"])\n            or payload["operation"] != "SET_AUTHORITY"\n            or payload["delegation_id"] != "payment-delegation-001"\n            or payload["state"] not in ("ACTIVE", "REVOKED")\n            or type(payload["expected_version"]) is not int\n            or not isinstance(payload["command_id"], str)\n            or not payload["command_id"]\n        ):\n            return denied\n\n        db.execute("BEGIN IMMEDIATE")\n        try:\n            if db.execute(\n                "SELECT 1 FROM commands WHERE command_id=?",\n                (payload["command_id"],)\n            ).fetchone():\n                db.rollback()\n                return denied\n\n            changed = db.execute(\n                "UPDATE authority SET state=?, version=version+1 "\n                "WHERE delegation_id=? AND version=?",\n                (\n                    payload["state"],\n                    "payment-delegation-001",\n                    payload["expected_version"],\n                )\n            )\n            if changed.rowcount != 1:\n                db.rollback()\n                return denied\n\n            db.execute(\n                "INSERT INTO commands VALUES (?)",\n                (payload["command_id"],)\n            )\n            db.commit()\n            return {"status": "APPLIED"}\n        except Exception:\n            db.rollback()\n            return denied\n    except Exception:\n        return denied\n\nprint(json.dumps({"ready": True, "pid": os.getpid()}), flush=True)\n\nfor line in sys.stdin:\n    try:\n        request = json.loads(line)\n        if not isinstance(request, dict):\n            result = {"status": "FAILED_CLOSED"}\n        elif request.get("action") == "READ_AUTHORITY":\n            state, version = current()\n            result = {"state": state, "version": version}\n        elif request.get("action") == "ADMINISTER_AUTHORITY":\n            result = apply(request)\n        else:\n            result = {"status": "FAILED_CLOSED"}\n    except Exception:\n        result = {"status": "FAILED_CLOSED"}\n    print(json.dumps(result), flush=True)\n'

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
            db.execute("BEGIN IMMEDIATE")

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

    def signed_revoke():
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization

        operator = Ed25519PrivateKey.generate()
        attacker = Ed25519PrivateKey.generate()

        public = operator.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw
        )

        admin_env = os.environ.copy()
        admin_env["VERIDIAN_TEST_AUTHORITY_DB"] = database
        admin_env["VERIDIAN_TEST_OPERATOR_PUBLIC_KEY"] = (
            base64.b64encode(public).decode("ascii")
        )

        def launch():
            proc = subprocess.Popen(
                [sys.executable, "-u", "-c", admin_worker_code],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=admin_env
            )
            return proc

        def exchange(proc, request):
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.flush()
            response = proc.stdout.readline()
            assert response, "Authority worker terminated"
            return json.loads(response)

        def envelope(identifier, state, version, key):
            payload = {
                "command_id": identifier,
                "delegation_id": "payment-delegation-001",
                "operation": "SET_AUTHORITY",
                "state": state,
                "expected_version": version
            }
            return {
                "action": "ADMINISTER_AUTHORITY",
                "authorization": {
                    "issuer": "TEST-OPERATOR",
                    "payload": payload,
                    "signature": sign_payload(key, payload)
                }
            }

        revoke = envelope(
            "payment-revoke-001", "REVOKED", 1, operator
        )

        forged = envelope(
            "forged-restore-001", "ACTIVE", 2, attacker
        )

        proc = launch()
        try:
            ready = json.loads(proc.stdout.readline())
            assert ready["ready"]
            first_pid = ready["pid"]

            assert exchange(proc, {
                "action": "READ_AUTHORITY"
            }) == {"state": "ACTIVE", "version": 1}

            assert exchange(proc, revoke)["status"] == "APPLIED"
            print("PASS: SIGNED OPERATOR PAYMENT REVOCATION")
        finally:
            proc.stdin.close()
            assert proc.wait(timeout=10) == 0

        proc = launch()
        try:
            ready = json.loads(proc.stdout.readline())
            assert ready["ready"]
            assert ready["pid"] != first_pid

            assert exchange(proc, {
                "action": "READ_AUTHORITY"
            }) == {"state": "REVOKED", "version": 2}
            print("PASS: PAYMENT AUTHORITY REVOCATION SURVIVED RESTART")

            assert exchange(proc, revoke)["status"] == "FAILED_CLOSED"
            assert exchange(proc, forged)["status"] == "FAILED_CLOSED"

            assert exchange(proc, {
                "action": "READ_AUTHORITY"
            }) == {"state": "REVOKED", "version": 2}
            print("PASS: ADMINISTRATIVE ATTACKS REJECTED")
        finally:
            proc.stdin.close()
            assert proc.wait(timeout=10) == 0

    def start_worker(mode):
        env = os.environ.copy()
        env["VERIDIAN_TEST_PAYMENT_DB"] = database
        # Operator changes durable authority, not worker environment.
        # Worker startup must not modify authority.
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
        signed_revoke()
        assert sys.platform == "darwin"

        protected_root = Path(database).resolve().parent

        profile = (
            "(version 1)\n"
            "(allow default)\n"
            "(deny file-write* (subpath "
            + json.dumps(str(protected_root)) + "))"
        )

        attacks = {
            "SQLITE MUTATION": (
                "with sqlite3.connect(sys.argv[1]) as db:\n"
                "    db.execute(\"UPDATE authority "
                "SET state='ACTIVE', version=3\")"
            ),
            "DATABASE DELETION": "os.remove(sys.argv[1])",
            "DATABASE RENAME": (
                "os.rename(sys.argv[1], sys.argv[1]+'.old')"
            )
        }

        original = Path(database).read_bytes()

        for name, action in attacks.items():
            result = subprocess.run(
                ["/usr/bin/sandbox-exec", "-p", profile,
                 sys.executable, "-c",
                 "import os, sys, sqlite3\n" + action,
                 database],
                capture_output=True,
                text=True,
                timeout=15
            )

            assert result.returncode != 0, name

            if name == "SQLITE MUTATION":
                assert "readonly" in result.stderr.lower() or \
                       "permission" in result.stderr.lower(), result.stderr
            else:
                assert "PermissionError" in result.stderr, result.stderr

            assert Path(database).read_bytes() == original

            with sqlite3.connect(database) as db:
                assert db.execute(
                    "SELECT state, version FROM authority "
                    "WHERE delegation_id=?",
                    ("payment-delegation-001",)
                ).fetchone() == ("REVOKED", 2)

            print("PASS: OS BLOCKED " + name)

        print("PASS: SHARED AUTHORITY DATABASE PRESERVED")
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

print("PASS: INDEPENDENT PAYMENT ENFORCEMENT REGRESSION")
