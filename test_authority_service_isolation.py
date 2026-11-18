"""Test-only isolated authority administration; no real payments."""
import base64
import json
import os
import subprocess
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bvp.trust_root import sign_payload

worker = r"""
import base64
import json
import os
import sqlite3
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from bvp.trust_root import verify_payload_signature

key = Ed25519PublicKey.from_public_bytes(
    base64.b64decode(os.environ["VERIDIAN_TEST_OPERATOR_PUBLIC_KEY"])
)

db = sqlite3.connect(":memory:", isolation_level=None)
db.execute("CREATE TABLE authority (id TEXT PRIMARY KEY, state TEXT, version INTEGER)")
db.execute("INSERT INTO authority VALUES ('delegation-001', 'ACTIVE', 1)")
db.execute("CREATE TABLE commands (command_id TEXT PRIMARY KEY)")

def current():
    return db.execute(
        "SELECT state, version FROM authority WHERE id='delegation-001'"
    ).fetchone()

def apply(request):
    denied = {"status": "FAILED_CLOSED"}
    try:
        auth = request["authorization"]
        payload = auth["payload"]

        if not isinstance(payload, dict):
            return denied

        if (
            auth["issuer"] != "TEST-OPERATOR"
            or not verify_payload_signature(key, payload, auth["signature"])
            or payload["operation"] != "SET_AUTHORITY"
            or payload["delegation_id"] != "delegation-001"
            or payload["state"] not in ("ACTIVE", "REVOKED")
            or type(payload["expected_version"]) is not int
            or not isinstance(payload["command_id"], str)
            or not payload["command_id"]
        ):
            return denied

        db.execute("BEGIN IMMEDIATE")
        try:
            if db.execute(
                "SELECT 1 FROM commands WHERE command_id=?",
                (payload["command_id"],)
            ).fetchone():
                db.rollback()
                return denied

            changed = db.execute(
                "UPDATE authority SET state=?, version=version+1 "
                "WHERE id=? AND version=?",
                (
                    payload["state"],
                    "delegation-001",
                    payload["expected_version"],
                )
            )
            if changed.rowcount != 1:
                db.rollback()
                return denied

            db.execute(
                "INSERT INTO commands VALUES (?)",
                (payload["command_id"],)
            )
            db.commit()
            return {"status": "APPLIED"}
        except Exception:
            db.rollback()
            return denied
    except Exception:
        return denied

print(json.dumps({"ready": True, "pid": os.getpid()}), flush=True)

for line in sys.stdin:
    try:
        request = json.loads(line)
        if not isinstance(request, dict):
            result = {"status": "FAILED_CLOSED"}
        elif request.get("action") == "READ_AUTHORITY":
            state, version = current()
            result = {"state": state, "version": version}
        elif request.get("action") == "ADMINISTER_AUTHORITY":
            result = apply(request)
        else:
            result = {"status": "FAILED_CLOSED"}
    except Exception:
        result = {"status": "FAILED_CLOSED"}
    print(json.dumps(result), flush=True)
"""

operator = Ed25519PrivateKey.generate()
attacker = Ed25519PrivateKey.generate()

public = operator.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)

env = os.environ.copy()
env["VERIDIAN_TEST_OPERATOR_PUBLIC_KEY"] = base64.b64encode(
    public
).decode("ascii")

process = subprocess.Popen(
    [sys.executable, "-u", "-c", worker],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env=env,
)

def exchange(request):
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()
    response = process.stdout.readline()
    assert response, "Authority worker terminated"
    return json.loads(response)

def command(identifier, state, version):
    return {
        "command_id": identifier,
        "delegation_id": "delegation-001",
        "operation": "SET_AUTHORITY",
        "state": state,
        "expected_version": version,
    }

def signed(payload, key=operator):
    return {
        "issuer": "TEST-OPERATOR",
        "payload": payload,
        "signature": sign_payload(key, payload),
    }

def apply(envelope):
    return exchange({
        "action": "ADMINISTER_AUTHORITY",
        "authorization": envelope,
    })["status"]

try:
    ready = json.loads(process.stdout.readline())
    assert ready["ready"] and ready["pid"] != os.getpid()
    print("PASS: INDEPENDENT AUTHORITY WORKER STARTED")

    assert exchange({"action": "READ_AUTHORITY"}) == {
        "state": "ACTIVE", "version": 1
    }

    revoke = signed(command("revoke-001", "REVOKED", 1))
    assert apply(revoke) == "APPLIED"
    print("PASS: OPERATOR REVOCATION ACCEPTED")

    assert apply(revoke) == "FAILED_CLOSED"
    print("PASS: REPLAY REJECTED")

    forged = signed(command("restore-forged", "ACTIVE", 2), attacker)
    assert apply(forged) == "FAILED_CLOSED"
    print("PASS: FORGED OPERATOR REJECTED")

    unsigned = {
        "issuer": "TEST-OPERATOR",
        "payload": command("restore-unsigned", "ACTIVE", 2),
        "signature": "INVALID",
    }
    assert apply(unsigned) == "FAILED_CLOSED"
    print("PASS: UNSIGNED AGENT RESTORATION REJECTED")

    stale = signed(command("restore-stale", "ACTIVE", 1))
    assert apply(stale) == "FAILED_CLOSED"
    print("PASS: STALE VERSION REJECTED")

    assert exchange({
        "action": "READ_AUTHORITY"
    }) == {"state": "REVOKED", "version": 2}

    print("PASS: REVOKED STATE PRESERVED")
    print("PASS: INDEPENDENT AUTHORITY PROCESS BASELINE")
finally:
    process.stdin.close()
    process.wait(timeout=10)
