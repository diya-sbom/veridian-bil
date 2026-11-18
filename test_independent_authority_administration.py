"""Test-only signed authority administration. No real payments."""
import sqlite3
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from bvp.trust_root import TrustedKeyRegistry, sign_payload

DELEGATION = "payment-delegation-001"
ISSUER = "VERIDIAN-TEST-OPERATOR"

operator_key = Ed25519PrivateKey.generate()
attacker_key = Ed25519PrivateKey.generate()

registry = TrustedKeyRegistry()
operator_key_id = registry.register(ISSUER, operator_key.public_key())

with tempfile.TemporaryDirectory() as folder:
    database = Path(folder) / "operator-authority.sqlite"

    with sqlite3.connect(database) as db:
        db.execute("""
            CREATE TABLE authority (
                delegation_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                version INTEGER NOT NULL
            )
        """)
        db.execute(
            "INSERT INTO authority VALUES (?, ?, ?)",
            (DELEGATION, "ACTIVE", 1),
        )
        db.execute("""
            CREATE TABLE applied_commands (
                command_id TEXT PRIMARY KEY
            )
        """)

    def current():
        with sqlite3.connect(database) as db:
            return db.execute(
                "SELECT state, version FROM authority WHERE delegation_id=?",
                (DELEGATION,),
            ).fetchone()

    def command(command_id, state, version):
        return {
            "command_id": command_id,
            "delegation_id": DELEGATION,
            "operation": "SET_AUTHORITY",
            "state": state,
            "expected_version": version,
        }

    def signed(payload, key=operator_key):
        return {
            "issuer": ISSUER,
            "key_id": operator_key_id,
            "payload": payload,
            "signature": sign_payload(key, payload),
        }

    def apply(envelope):
        try:
            payload = envelope["payload"]
            if not isinstance(payload, dict):
                return "FAILED_CLOSED"

            if (
                envelope["issuer"] != ISSUER
                or envelope["key_id"] != operator_key_id
                or not registry.verify(
                    envelope["issuer"],
                    envelope["key_id"],
                    payload,
                    envelope["signature"],
                )
                or payload["operation"] != "SET_AUTHORITY"
                or payload["delegation_id"] != DELEGATION
                or payload["state"] not in ("ACTIVE", "REVOKED")
                or type(payload["expected_version"]) is not int
                or not isinstance(payload["command_id"], str)
                or not payload["command_id"]
            ):
                return "FAILED_CLOSED"

            with sqlite3.connect(database) as db:
                db.execute("BEGIN IMMEDIATE")

                if db.execute(
                    "SELECT 1 FROM applied_commands WHERE command_id=?",
                    (payload["command_id"],),
                ).fetchone():
                    return "FAILED_CLOSED"

                changed = db.execute(
                    """UPDATE authority
                       SET state=?, version=version+1
                       WHERE delegation_id=? AND version=?""",
                    (
                        payload["state"],
                        DELEGATION,
                        payload["expected_version"],
                    ),
                )
                if changed.rowcount != 1:
                    return "FAILED_CLOSED"

                db.execute(
                    "INSERT INTO applied_commands VALUES (?)",
                    (payload["command_id"],),
                )
            return "APPLIED"
        except (KeyError, TypeError, ValueError, sqlite3.Error):
            return "FAILED_CLOSED"

    revoke = signed(command("operator-revoke-001", "REVOKED", 1))
    assert apply(revoke) == "APPLIED"
    assert current() == ("REVOKED", 2)
    print("PASS: TRUSTED OPERATOR REVOCATION PERSISTED")

    assert apply(revoke) == "FAILED_CLOSED"
    print("PASS: REPLAYED OPERATOR COMMAND REJECTED")

    forged = signed(
        command("agent-restore-001", "ACTIVE", 2),
        attacker_key,
    )
    assert apply(forged) == "FAILED_CLOSED"
    print("PASS: FORGED OPERATOR SIGNATURE REJECTED")

    unapproved = {
        "issuer": ISSUER,
        "key_id": operator_key_id,
        "payload": command("agent-restore-002", "ACTIVE", 2),
        "signature": "NOT-A-VALID-SIGNATURE",
        "authority_state": "ACTIVE",
    }
    assert apply(unapproved) == "FAILED_CLOSED"
    print("PASS: AGENT AUTHORITY CLAIM REJECTED")

    stale = signed(command("operator-stale-001", "ACTIVE", 1))
    assert apply(stale) == "FAILED_CLOSED"
    print("PASS: STALE AUTHORITY VERSION REJECTED")

    assert current() == ("REVOKED", 2)
    print("PASS: REVOKED AUTHORITY REMAINS UNCHANGED")
    print("PASS: SIGNED AUTHORITY ADMINISTRATION BASELINE")
