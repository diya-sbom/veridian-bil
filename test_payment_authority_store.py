"""Test-only authority store. No real payments."""
import sqlite3
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "authority.sqlite"

    # Operator-controlled initialization.
    with sqlite3.connect(path) as db:
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

    def read_authority():
        with sqlite3.connect(path) as db:
            return db.execute(
                "SELECT state, version FROM authority WHERE delegation_id=?",
                ("payment-delegation-001",),
            ).fetchone()

    assert read_authority() == ("ACTIVE", 1)
    print("PASS: CURRENT ACTIVE AUTHORITY READ")

    # Simulate revocation by the authority operator.
    with sqlite3.connect(path) as db:
        db.execute("""
            UPDATE authority
            SET state='REVOKED', version=version+1
            WHERE delegation_id=?
        """, ("payment-delegation-001",))

    assert read_authority() == ("REVOKED", 2)
    print("PASS: REVOCATION PERSISTED")

    # Restart-style read from a new database connection.
    assert read_authority()[0] == "REVOKED"
    print("PASS: NEW CONNECTION OBSERVES REVOCATION")

print("PASS: TEST-ONLY DURABLE AUTHORITY STORE")
