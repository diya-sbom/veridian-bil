"""Test-only concurrent authority/revocation transaction proof."""
import sqlite3
import tempfile
import threading
from pathlib import Path

def setup(path):
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE authority (id TEXT PRIMARY KEY, state TEXT)")
        db.execute("INSERT INTO authority VALUES ('delegation-001', 'ACTIVE')")
        db.execute("CREATE TABLE payments (id TEXT PRIMARY KEY)")

def run_case(revocation_first):
    with tempfile.TemporaryDirectory() as folder:
        path = str(Path(folder) / "state.sqlite")
        setup(path)
        locked = threading.Event()
        release = threading.Event()
        result = {}

        def revoke():
            with sqlite3.connect(path, timeout=10) as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "UPDATE authority SET state='REVOKED' WHERE id='delegation-001'"
                )
                locked.set()
                assert release.wait(5)
                db.commit()

        def pay():
            with sqlite3.connect(path, timeout=10) as db:
                db.execute("BEGIN IMMEDIATE")
                state = db.execute(
                    "SELECT state FROM authority WHERE id='delegation-001'"
                ).fetchone()[0]
                if state == "ACTIVE":
                    db.execute("INSERT INTO payments VALUES ('payment-001')")
                    result["status"] = "COMPLETED"
                else:
                    result["status"] = "FAILED_CLOSED"
                db.commit()

        if revocation_first:
            a = threading.Thread(target=revoke)
            b = threading.Thread(target=pay)
            a.start()
            assert locked.wait(5)
            b.start()
            release.set()
        else:
            # Establish the payment's serialization point first.
            with sqlite3.connect(path, timeout=10) as db:
                db.execute("BEGIN IMMEDIATE")
                state = db.execute(
                    "SELECT state FROM authority WHERE id='delegation-001'"
                ).fetchone()[0]
                assert state == "ACTIVE"
                db.execute("INSERT INTO payments VALUES ('payment-001')")
                db.commit()
            result["status"] = "COMPLETED"
            a = threading.Thread(target=revoke)
            a.start()
            assert locked.wait(5)
            release.set()
            b = None

        a.join(10)
        if b is not None:
            b.join(10)
        assert not a.is_alive()
        assert b is None or not b.is_alive()

        with sqlite3.connect(path) as db:
            count = db.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
            state = db.execute("SELECT state FROM authority").fetchone()[0]

        assert state == "REVOKED"
        expected = ("FAILED_CLOSED", 0) if revocation_first else ("COMPLETED", 1)
        assert (result["status"], count) == expected, (result, count)
        return expected

assert run_case(True) == ("FAILED_CLOSED", 0)
print("PASS: REVOCATION FIRST BLOCKED PAYMENT")

assert run_case(False) == ("COMPLETED", 1)
print("PASS: PAYMENT COMMITTED BEFORE REVOCATION")

print("PASS: SQLITE AUTHORITY TRANSACTION ORDERING")
