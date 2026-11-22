admin_worker_code = '\nimport base64\nimport json\nimport os\nimport sqlite3\nimport sys\n\nfrom cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey\nfrom bvp.trust_root import verify_payload_signature\n\nkey = Ed25519PublicKey.from_public_bytes(\n    base64.b64decode(os.environ["VERIDIAN_TEST_OPERATOR_PUBLIC_KEY"])\n)\n\ndb = sqlite3.connect(os.environ["VERIDIAN_TEST_AUTHORITY_DB"], isolation_level=None)\ndb.execute("CREATE TABLE IF NOT EXISTS commands (command_id TEXT PRIMARY KEY, delegation_id TEXT NOT NULL, resulting_version INTEGER NOT NULL, signed_command TEXT NOT NULL, UNIQUE(delegation_id, resulting_version))")\n\ndef current():\n    return db.execute(\n        "SELECT state, version FROM authority WHERE delegation_id=\'payment-delegation-001\'"\n    ).fetchone()\n\ndef apply(request):\n    denied = {"status": "FAILED_CLOSED"}\n    try:\n        auth = request["authorization"]\n        payload = auth["payload"]\n\n        if not isinstance(payload, dict):\n            return denied\n\n        if (\n            auth["issuer"] != "TEST-OPERATOR"\n            or not verify_payload_signature(key, payload, auth["signature"])\n            or payload["operation"] != "SET_AUTHORITY"\n            or payload["delegation_id"] != "payment-delegation-001"\n            or payload["state"] not in ("ACTIVE", "REVOKED")\n            or type(payload["expected_version"]) is not int\n            or not isinstance(payload["command_id"], str)\n            or not payload["command_id"]\n        ):\n            return denied\n\n        db.execute("BEGIN IMMEDIATE")\n        try:\n            if db.execute(\n                "SELECT 1 FROM commands WHERE command_id=?",\n                (payload["command_id"],)\n            ).fetchone():\n                db.rollback()\n                return denied\n\n            changed = db.execute(\n                "UPDATE authority SET state=?, version=version+1 "\n                "WHERE delegation_id=? AND version=?",\n                (\n                    payload["state"],\n                    "payment-delegation-001",\n                    payload["expected_version"],\n                )\n            )\n            if changed.rowcount != 1:\n                db.rollback()\n                return denied\n\n            db.execute("INSERT INTO commands VALUES (?, ?, ?, ?)", (payload["command_id"], payload["delegation_id"], payload["expected_version"] + 1, json.dumps(auth, sort_keys=True)))\n            db.commit()\n            return {"status": "APPLIED"}\n        except Exception:\n            db.rollback()\n            return denied\n    except Exception:\n        return denied\n\nprint(json.dumps({"ready": True, "pid": os.getpid()}), flush=True)\n\nfor line in sys.stdin:\n    try:\n        request = json.loads(line)\n        if not isinstance(request, dict):\n            result = {"status": "FAILED_CLOSED"}\n        elif request.get("action") == "READ_AUTHORITY":\n            state, version = current()\n            result = {"state": state, "version": version}\n        elif request.get("action") == "ADMINISTER_AUTHORITY":\n            result = apply(request)\n        else:\n            result = {"status": "FAILED_CLOSED"}\n    except Exception:\n        result = {"status": "FAILED_CLOSED"}\n    print(json.dumps(result), flush=True)\n'

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

worker_code = '\nfrom cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey\nfrom cryptography.hazmat.primitives import serialization\nfrom bvp.trust_root import sign_payload, public_key_id\n\nimport os\nimport base64\n\nevidence_private_key = Ed25519PrivateKey.from_private_bytes(\n    base64.b64decode(\n        os.environ.pop("VERIDIAN_TEST_EVIDENCE_KEY")\n    )\n)\nevidence_public_key = evidence_private_key.public_key()\nevidence_key_id = public_key_id(evidence_public_key)\n\n\nimport base64\nimport contextlib\nimport io\nimport json\nimport os\nimport runpy\nimport sqlite3\nimport sys\nfrom datetime import datetime, timezone\n\nfrom cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey\nfrom bvp.trust_root import verify_payload_signature\nfrom executor.guarded_execution import execute_with_current_authority\n\nwith contextlib.redirect_stdout(io.StringIO()):\n    f = runpy.run_path("test_guarded_execution_revocation.py")\n\ndecision = f["payment"]\n# Authority is read from the service database at redemption.\n\nstates = {\n    "ACTIVE": ("active_state", "active_state_boundary"),\n    "REVOKED": ("revoked_state", "revoked_state_boundary"),\n}\n\ntry:\n    trusted = Ed25519PublicKey.from_public_bytes(\n        base64.b64decode(\n            os.environ["VERIDIAN_TEST_TRUSTED_PUBLIC_KEY"],\n            validate=True,\n        )\n    )\nexcept Exception:\n    trusted = None\n\ndatabase = os.environ["VERIDIAN_TEST_PAYMENT_DB"]\n\nwith sqlite3.connect(database) as db:\n    db.execute("""\n        CREATE TABLE IF NOT EXISTS payments (\n            authorization_id TEXT PRIMARY KEY,\n            decision_id TEXT NOT NULL,\n            payee TEXT NOT NULL,\n            amount INTEGER NOT NULL\n        )\n    """)\n\n\nwith sqlite3.connect(database) as db:\n    db.execute("""\n        CREATE TABLE IF NOT EXISTS denial_evidence (\n            evidence_id TEXT PRIMARY KEY,\n            authorization_id TEXT NOT NULL,\n            signed_evidence TEXT NOT NULL,\n            key_id TEXT NOT NULL,\n            signature TEXT NOT NULL\n        )\n    """)\n\ndef redeem(request):\n    denied = {"status": "FAILED_CLOSED"}\n\n    if not isinstance(request, dict):\n        return denied\n\n    if trusted is None:\n        return denied\n\n    try:\n        authorization = request["authorization"]\n        payload = authorization["payload"]\n        signature = authorization["signature"]\n\n        if not isinstance(payload, dict):\n            return denied\n\n        if not verify_payload_signature(trusted, payload, signature):\n            return denied\n\n        expires = datetime.fromisoformat(payload["expires_at"])\n\n        if expires.tzinfo is None:\n            return denied\n\n        if datetime.now(timezone.utc) >= expires:\n            return denied\n\n        if not (\n            request.get("action") == "EXECUTE_PAYMENT"\n            and payload.get("action") == "EXECUTE_PAYMENT"\n            and payload.get("audience") == "MOCK-PAYMENT-SERVICE"\n            and payload.get("decision_id") == decision.decision_id\n            and request.get("payee") == payload.get("payee")\n            and payload.get("payee") == decision.governed_resource\n            and type(request.get("amount")) is int\n            and type(payload.get("amount")) is int\n            and request["amount"] == payload["amount"]\n            and payload["amount"] == decision.requested_authority_units\n            and isinstance(payload.get("authorization_id"), str)\n            and bool(payload["authorization_id"])\n        ):\n            return denied\n\n\n        with sqlite3.connect(database, timeout=10) as db:\n            db.execute("BEGIN IMMEDIATE")\n\n            # Read operator-owned authority under the payment lock.\n            current = db.execute(\n                "SELECT state, version FROM authority WHERE delegation_id=?",\n                ("payment-delegation-001",),\n            ).fetchone()\n\n            if current is None or current[0] not in states:\n                db.rollback()\n                return denied\n\n            state_key, boundary_key = states[current[0]]\n\n            existing = db.execute(\n                "SELECT 1 FROM payments WHERE authorization_id=?",\n                (payload["authorization_id"],)\n            ).fetchone()\n\n            if existing:\n                db.rollback()\n                return denied\n\n            with contextlib.redirect_stdout(io.StringIO()):\n                verification, _, record, execution = (\n                    execute_with_current_authority(\n                        decision,\n                        f["gov"],\n                        f["boundary"],\n                        f["responsibility_chain"],\n                        f["authority_evidence"],\n                        f["authority_boundary_receipt"],\n                        f[state_key],\n                        f[boundary_key],\n                        f["authorization_time"],\n                        f["trusted_key_registry"],\n                    )\n                )\n\n            if not (\n                verification.status == "VERIFIED"\n                and verification.verified_action == "EXECUTE_PAYMENT"\n                and record.status == "VERIFIED"\n                and record.verified_action == "EXECUTE_PAYMENT"\n                and execution.status == "EXECUTED"\n                and execution.action == "EXECUTE_PAYMENT"\n            ):\n                if current[0] == "REVOKED":\n                    revocation = db.execute(\n                        "SELECT command_id, signed_command "\n                        "FROM commands WHERE delegation_id=? "\n                        "AND resulting_version=?",\n                        ("payment-delegation-001", current[1])\n                    ).fetchone()\n\n                    if revocation is None:\n                        db.rollback()\n                        return denied\n\n                    signed_revocation = json.loads(revocation[1])\n\n                    denial_evidence = {\n                        "schema": "veridian.payment-denial.v1",\n                        "evidence_id": __import__("uuid").uuid4().hex,\n                        "authorization": request["authorization"],\n                        "authorization_id": payload["authorization_id"],\n                        "decision_id": decision.decision_id,\n                        "delegation_id": "payment-delegation-001",\n                        "payee": payload["payee"],\n                        "amount": payload["amount"],\n                        "authority_state": current[0],\n                        "authority_version": current[1],\n                        "revocation_command_id": revocation[0],\n                        "signed_revocation": signed_revocation,\n                        "status": "FAILED_CLOSED",\n                        "reason": "CURRENT_AUTHORITY_REVOKED",\n                        "verification_status": verification.status,\n                        "execution_status": execution.status,\n                        "observed_at": datetime.now(timezone.utc).isoformat()\n                    }\n\n                    signature = sign_payload(\n                        evidence_private_key, denial_evidence\n                    )\n\n                    db.execute(\n                        "INSERT INTO denial_evidence "\n                        "VALUES (?, ?, ?, ?, ?)",\n                        (\n                            denial_evidence["evidence_id"],\n                            payload["authorization_id"],\n                            json.dumps(denial_evidence, sort_keys=True),\n                            evidence_key_id,\n                            signature\n                        )\n                    )\n\n                    db.commit()\n\n                    return {\n                        "status": "FAILED_CLOSED",\n                        "evidence": denial_evidence,\n                        "evidence_key_id": evidence_key_id,\n                        "evidence_signature": signature\n                    }\n\n                db.rollback()\n                return denied\n\n            db.execute(\n                """INSERT INTO payments\n                   (authorization_id, decision_id, payee, amount)\n                   VALUES (?, ?, ?, ?)""",\n                (\n                    payload["authorization_id"],\n                    decision.decision_id,\n                    payload["payee"],\n                    payload["amount"],\n                ),\n            )\n            db.commit()\n\n        return {"status": "COMPLETED"}\n\n    except Exception:\n        return denied\n\n# The service announces its own decision identity.\nprint(json.dumps({\n    "decision_id": decision.decision_id,\n    "payee": decision.governed_resource,\n    "amount": decision.requested_authority_units,\n}), flush=True)\n\nfor line in sys.stdin:\n    try:\n        response = redeem(json.loads(line))\n    except Exception:\n        response = {"status": "FAILED_CLOSED"}\n    print(json.dumps(response), flush=True)\n'

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
            from bvp.trust_root import verify_payload_signature

            with sqlite3.connect(database) as db:
                rows = db.execute(
                    "SELECT command_id, delegation_id, "
                    "resulting_version, signed_command "
                    "FROM commands"
                ).fetchall()

            assert len(rows) == 1

            command_id, delegation_id, version, stored = rows[0]
            stored = json.loads(stored)

            assert command_id == "payment-revoke-001"
            assert delegation_id == "payment-delegation-001"
            assert version == 2

            assert stored == revoke["authorization"]

            assert verify_payload_signature(
                operator.public_key(),
                stored["payload"],
                stored["signature"]
            )

            assert stored["payload"]["state"] == "REVOKED"
            assert stored["payload"]["expected_version"] + 1 == version

            print("PASS: COMPLETE SIGNED REVOCATION PRESERVED")
            print("PASS: DURABLE REVOCATION SIGNATURE VERIFIED")
            print("PASS: REVOCATION VERSION LINKAGE VERIFIED")
            print("PASS: REJECTED COMMANDS NOT PERSISTED")
            return operator.public_key(), stored
        finally:
            proc.stdin.close()
            assert proc.wait(timeout=10) == 0

    trusted_evidence_key = Ed25519PrivateKey.generate()
    trusted_evidence_public = trusted_evidence_key.public_key()

    def start_worker(mode):
        env = os.environ.copy()
        env["VERIDIAN_TEST_PAYMENT_DB"] = database
        env["VERIDIAN_TEST_EVIDENCE_KEY"] = (
            base64.b64encode(
                trusted_evidence_key.private_bytes(
                    serialization.Encoding.Raw,
                    serialization.PrivateFormat.Raw,
                    serialization.NoEncryption()
                )
            ).decode("ascii")
        )
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
        trusted_operator_public, expected_revocation = signed_revoke()
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
        from bvp.trust_root import (
            verify_payload_signature, public_key_id
        )
        import copy

        active.stdin.write(json.dumps(pending) + "\n")
        active.stdin.flush()

        response = json.loads(active.stdout.readline())

        assert response["status"] == "FAILED_CLOSED"
        evidence = response["evidence"]
        signature = response["evidence_signature"]

        assert response["evidence_key_id"] == public_key_id(
            trusted_evidence_public
        )

        assert verify_payload_signature(
            trusted_evidence_public, evidence, signature
        )
        print("PASS: TRUSTED DENIAL SIGNATURE VERIFIED")

        assert evidence["authorization"] == pending["authorization"]
        payload = pending["authorization"]["payload"]

        assert evidence["authorization_id"] == payload["authorization_id"]
        assert evidence["decision_id"] == payload["decision_id"]
        assert evidence["payee"] == payload["payee"]
        assert evidence["amount"] == payload["amount"]
        assert evidence["delegation_id"] == "payment-delegation-001"

        print("PASS: EXACT PAYMENT AUTHORIZATION BOUND")

        assert evidence["authority_state"] == "REVOKED"
        assert evidence["authority_version"] == 2
        assert evidence["status"] == "FAILED_CLOSED"
        assert evidence["reason"] == "CURRENT_AUTHORITY_REVOKED"

        print("PASS: REVOKED AUTHORITY VERSION BOUND")
        def verify_revocation_link(item):
            try:
                revocation = item["signed_revocation"]
                command = revocation["payload"]

                return (
                    revocation["issuer"] == "TEST-OPERATOR"
                    and verify_payload_signature(
                        trusted_operator_public,
                        command,
                        revocation["signature"]
                    )
                    and command["operation"] == "SET_AUTHORITY"
                    and command["state"] == "REVOKED"
                    and command["delegation_id"] == item["delegation_id"]
                    and command["command_id"] == item["revocation_command_id"]
                    and type(command["expected_version"]) is int
                    and command["expected_version"] + 1 == item["authority_version"]
                    and item["authority_state"] == "REVOKED"
                )
            except Exception:
                return False

        assert evidence["signed_revocation"] == expected_revocation
        assert verify_revocation_link(evidence)

        print("PASS: AUTHENTICATED REVOCATION LINK VERIFIED")

        missing = copy.deepcopy(evidence)
        del missing["signed_revocation"]
        assert not verify_revocation_link(missing)

        print("PASS: MISSING REVOCATION REJECTED")

        forged = copy.deepcopy(evidence)
        forged["signed_revocation"]["signature"] = sign_payload(
            Ed25519PrivateKey.generate(),
            forged["signed_revocation"]["payload"]
        )
        assert not verify_revocation_link(forged)

        print("PASS: FORGED REVOCATION REJECTED")

        for field, value in [
            ("revocation_command_id", "substituted-command"),
            ("delegation_id", "another-delegation"),
            ("authority_version", 3)
        ]:
            changed = copy.deepcopy(evidence)
            changed[field] = value
            assert not verify_revocation_link(changed)
            print("PASS: REVOCATION LINK MISMATCH REJECTED: " + field)

        print("PASS: AUTHENTICATED REVOCATION LINKAGE")

        for field, value in [
            ("authority_state", "ACTIVE"),
            ("authority_version", 1),
            ("amount", evidence["amount"] + 1),
            ("status", "COMPLETED"),
            ("decision_id", "substituted-decision")
        ]:
            tampered = copy.deepcopy(evidence)
            tampered[field] = value

            assert not verify_payload_signature(
                trusted_evidence_public, tampered, signature
            )

            print("PASS: EVIDENCE TAMPERING REJECTED: " + field)

        forged_key = Ed25519PrivateKey.generate()
        forged_signature = sign_payload(forged_key, evidence)

        assert not verify_payload_signature(
            trusted_evidence_public, evidence, forged_signature
        )

        print("PASS: FORGED EVIDENCE SIGNATURE REJECTED")
        print("PASS: AUTHENTICATED PAYMENT DENIAL EVIDENCE")
        print("PASS: POST-ISSUANCE REVOCATION BLOCKED PAYMENT")
    finally:
        active.stdin.close()
        assert active.wait(timeout=10) == 0

    assert active.poll() == 0
    print("PASS: ORIGINAL PAYMENT WORKER TERMINATED")

    with sqlite3.connect(database) as db:
        rows = db.execute(
            "SELECT authorization_id, signed_evidence, "
            "key_id, signature FROM denial_evidence "
            "WHERE evidence_id=?",
            (evidence["evidence_id"],)
        ).fetchall()

        unauthorized = db.execute(
            "SELECT COUNT(*) FROM payments "
            "WHERE authorization_id=?",
            (evidence["authorization_id"],)
        ).fetchone()[0]

    assert len(rows) == 1

    authorization_id, stored_json, key_id, stored_signature = rows[0]
    stored_evidence = json.loads(stored_json)

    assert authorization_id == evidence["authorization_id"]
    assert stored_evidence == evidence
    assert stored_signature == signature
    assert key_id == public_key_id(trusted_evidence_public)

    print("PASS: DENIAL EVIDENCE SURVIVED WORKER TERMINATION")

    assert verify_payload_signature(
        trusted_evidence_public,
        stored_evidence,
        stored_signature
    )

    print("PASS: PERSISTED DENIAL SIGNATURE VERIFIED")

    assert verify_revocation_link(stored_evidence)

    print("PASS: PERSISTED REVOCATION LINK VERIFIED")

    assert unauthorized == 0

    print("PASS: DENIED AUTHORIZATION NEVER COMMITTED")
    print("PASS: DURABLE DENIAL EVIDENCE VERIFIED")
    with sqlite3.connect(database) as db:
        before_count = db.execute(
            "SELECT COUNT(*) FROM denial_evidence"
        ).fetchone()[0]

        db.execute("""
            CREATE TRIGGER reject_denial_evidence
            BEFORE INSERT ON denial_evidence
            BEGIN
                SELECT RAISE(ABORT, 'TEST_STORAGE_FAILURE');
            END
        """)

    failure_worker, failure_identity = start_worker("REVOKED")

    failure_request = payment_request(failure_identity)

    try:
        output, errors = failure_worker.communicate(
            input=json.dumps(failure_request) + "\n",
            timeout=15
        )
    except subprocess.TimeoutExpired:
        failure_worker.kill()
        failure_worker.communicate()
        raise AssertionError("STOP: Worker response timeout")

    assert failure_worker.returncode == 0, errors

    failure_response = json.loads(output.strip())

    assert failure_response["status"] == "FAILED_CLOSED"
    assert "evidence" not in failure_response

    with sqlite3.connect(database) as db:
        assert db.execute(
            "SELECT COUNT(*) FROM denial_evidence"
        ).fetchone()[0] == before_count

        assert db.execute(
            "SELECT COUNT(*) FROM payments"
        ).fetchone()[0] == 1

        assert db.execute(
            "SELECT state, version FROM authority "
            "WHERE delegation_id=?",
            ("payment-delegation-001",)
        ).fetchone() == ("REVOKED", 2)

        db.execute("DROP TRIGGER reject_denial_evidence")

    print("PASS: EVIDENCE STORAGE FAILURE BLOCKED PAYMENT")
    print("PASS: NO FALSE EVIDENCE RETURNED")
    print("PASS: NO PARTIAL EVIDENCE COMMITTED")
    print("PASS: REVOKED AUTHORITY PRESERVED")

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
