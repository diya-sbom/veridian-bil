"""Test-only authority service signing and independent receipt verification."""

import base64
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from bvp.trust_root import sign_payload, verify_payload_signature


def encode_public(key):
    return base64.b64encode(
        key.public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw
        )
    ).decode("ascii")


def decode_public(value):
    return serialization.load_raw_public_key(
        base64.b64decode(value)
    ) if hasattr(serialization, "load_raw_public_key") else (
        __import__(
            "cryptography.hazmat.primitives.asymmetric.ed25519",
            fromlist=["Ed25519PublicKey"]
        ).Ed25519PublicKey.from_public_bytes(
            base64.b64decode(value)
        )
    )


def service(db_path, operator_public):
    # Service signing private key stays inside this child process.
    service_key = Ed25519PrivateKey.generate()

    with sqlite3.connect(db_path) as db:
        db.execute(
            "CREATE TABLE authority "
            "(delegation_id TEXT PRIMARY KEY, "
            "state TEXT NOT NULL, version INTEGER NOT NULL)"
        )
        db.execute(
            "INSERT INTO authority VALUES (?, ?, ?)",
            ("delegation-001", "ACTIVE", 1)
        )
        db.execute(
            "CREATE TABLE application_receipts "
            "(command_id TEXT PRIMARY KEY, "
            "payload TEXT NOT NULL, signature TEXT NOT NULL)"
        )
        db.execute(
            "CREATE TABLE signed_commands "
            "(command_id TEXT PRIMARY KEY, "
            "payload TEXT NOT NULL, signature TEXT NOT NULL)"
        )

    print(json.dumps({
        "ready": True,
        "service_public": encode_public(service_key.public_key())
    }), flush=True)

    for line in sys.stdin:
        try:
            request = json.loads(line)
            command = request["command"]
            signature = request["signature"]

            assert verify_payload_signature(
                operator_public, command, signature
            )
            assert command["operation"] == "REVOKE"
            assert command["delegation_id"] == "delegation-001"
            assert command["expected_version"] == 1

            with sqlite3.connect(db_path) as db:
                db.execute("BEGIN IMMEDIATE")
                changed = db.execute(
                    "UPDATE authority SET state='REVOKED', "
                    "version=version+1 "
                    "WHERE delegation_id=? AND state='ACTIVE' "
                    "AND version=?",
                    (
                        command["delegation_id"],
                        command["expected_version"]
                    )
                )
                assert changed.rowcount == 1

                # Controlled failure-injection test.
                if request.get("inject_storage_failure"):
                    raise RuntimeError("Injected storage failure")

                receipt = {
                    "schema": "veridian.authority-application.v1",
                    "command_id": command["command_id"],
                    "delegation_id": command["delegation_id"],
                    "previous_version": 1,
                    "resulting_version": 2,
                    "resulting_state": "REVOKED",
                    "applied_at": datetime.now(
                        timezone.utc
                    ).isoformat()
                }

                signed_receipt = sign_payload(service_key, receipt)

                db.execute(
                    "INSERT INTO signed_commands VALUES (?, ?, ?)",
                    (
                        command["command_id"],
                        json.dumps(command, sort_keys=True),
                        signature
                    )
                )
                db.execute(
                    "INSERT INTO application_receipts VALUES (?, ?, ?)",
                    (
                        command["command_id"],
                        json.dumps(receipt, sort_keys=True),
                        signed_receipt
                    )
                )

                db.commit()

            response = {"status": "APPLIED"}

        except Exception:
            response = {"status": "FAILED_CLOSED"}

        print(json.dumps(response), flush=True)


def verify_database(db_path, operator_public, service_public):
    try:
        with sqlite3.connect(db_path) as db:
            state = db.execute(
                "SELECT state, version FROM authority "
                "WHERE delegation_id='delegation-001'"
            ).fetchone()

            assert state == ("REVOKED", 2)

            rows = db.execute(
                "SELECT command_id, payload, signature "
                "FROM application_receipts"
            ).fetchall()
            assert len(rows) == 1

            command_id, raw_receipt, receipt_signature = rows[0]
            receipt = json.loads(raw_receipt)

            assert verify_payload_signature(
                service_public, receipt, receipt_signature
            )

            assert receipt["command_id"] == command_id
            assert receipt["delegation_id"] == "delegation-001"
            assert receipt["previous_version"] == 1
            assert receipt["resulting_version"] == state[1]
            assert receipt["resulting_state"] == state[0]

            row = db.execute(
                "SELECT payload, signature FROM signed_commands "
                "WHERE command_id=?",
                (command_id,)
            ).fetchone()

            assert row is not None
            command, command_signature = row
            command = json.loads(command)

            assert verify_payload_signature(
                operator_public, command, command_signature
            )

            assert command["command_id"] == command_id
            assert command["delegation_id"] == receipt["delegation_id"]
            assert command["expected_version"] + 1 == state[1]
            assert command["operation"] == "REVOKE"

        return True
    except Exception:
        return False


def main():
    with tempfile.TemporaryDirectory() as folder:
        db_path = str(Path(folder) / "authority.sqlite")

        operator_key = Ed25519PrivateKey.generate()
        operator_public = encode_public(operator_key.public_key())

        env = os.environ.copy()
        env["VERIDIAN_TEST_OPERATOR_PUBLIC"] = operator_public

        proc = subprocess.Popen(
            [sys.executable, "-u", __file__, "--service", db_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )

        try:
            ready = json.loads(proc.stdout.readline())
            assert ready["ready"] is True

            service_public = ready["service_public"]

            assert operator_public != service_public
            print("PASS: DISTINCT AUTHORITY SERVICE IDENTITY")

            command = {
                "command_id": "revoke-001",
                "delegation_id": "delegation-001",
                "operation": "REVOKE",
                "expected_version": 1
            }

            request = {
                "command": command,
                "signature": sign_payload(operator_key, command)
            }

            def send(message):
                proc.stdin.write(json.dumps(message) + "\n")
                proc.stdin.flush()
                return json.loads(proc.stdout.readline())

            failed = dict(request, inject_storage_failure=True)
            assert send(failed)["status"] == "FAILED_CLOSED"

            with sqlite3.connect(db_path) as db:
                assert db.execute(
                    "SELECT state, version FROM authority"
                ).fetchone() == ("ACTIVE", 1)
                assert db.execute(
                    "SELECT COUNT(*) FROM application_receipts"
                ).fetchone()[0] == 0

            print("PASS: STORAGE FAILURE ROLLED BACK AUTHORITY")

            assert send(request)["status"] == "APPLIED"
            print("PASS: SIGNED REVOCATION APPLICATION COMMITTED")

            assert send(request)["status"] == "FAILED_CLOSED"
            print("PASS: REVOCATION COMMAND REPLAY REJECTED")

            forged = dict(
                request,
                signature=sign_payload(
                    Ed25519PrivateKey.generate(), command
                )
            )
            assert send(forged)["status"] == "FAILED_CLOSED"
            print("PASS: FORGED OPERATOR COMMAND REJECTED")

            assert verify_database(
                db_path,
                decode_public(operator_public),
                decode_public(service_public)
            )
            print("PASS: INDEPENDENT RECEIPT SIGNATURE VERIFIED")

            with sqlite3.connect(db_path) as db:
                original = db.execute(
                    "SELECT payload FROM application_receipts"
                ).fetchone()[0]

                altered = json.loads(original)
                altered["resulting_state"] = "ACTIVE"

                db.execute(
                    "UPDATE application_receipts SET payload=?",
                    (json.dumps(altered),)
                )

            assert not verify_database(
                db_path,
                decode_public(operator_public),
                decode_public(service_public)
            )
            print("PASS: ALTERED APPLICATION RECEIPT REJECTED")

            with sqlite3.connect(db_path) as db:
                db.execute(
                    "UPDATE application_receipts SET payload=?",
                    (original,)
                )

            assert verify_database(
                db_path,
                decode_public(operator_public),
                decode_public(service_public)
            )
            print("PASS: ORIGINAL SIGNED RECEIPT PRESERVED")

            print("PASS: AUTHORITY SERVICE SIGNING BASELINE")

        finally:
            proc.stdin.close()
            proc.wait(timeout=10)
            if proc.returncode != 0:
                print(proc.stderr.read())
                raise AssertionError("Authority worker failed")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--service":
        service(
            sys.argv[2],
            decode_public(
                os.environ["VERIDIAN_TEST_OPERATOR_PUBLIC"]
            )
        )
    else:
        main()
