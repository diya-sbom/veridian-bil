
import tempfile
import subprocess
import sqlite3
import sys
import json
from pathlib import Path

assert sys.platform == "darwin", "Requires macOS"
assert Path("/usr/bin/sandbox-exec").exists()

with tempfile.TemporaryDirectory() as folder:
    root = Path(folder).resolve()
    protected = root / "protected"
    protected.mkdir()

    database = protected / "authority.sqlite"
    replacement = root / "replacement.sqlite"

    for path, state, version in [
        (database, "REVOKED", 2),
        (replacement, "ACTIVE", 3)
    ]:
        with sqlite3.connect(path) as db:
            db.execute(
                "CREATE TABLE authority "
                "(state TEXT, version INTEGER)"
            )
            db.execute(
                "INSERT INTO authority VALUES (?, ?)",
                (state, version)
            )

    profile = (
        "(version 1)\n"
        "(allow default)\n"
        "(deny file-write* (subpath "
        + json.dumps(str(protected)) + "))"
    )

    mutation = (
        "with sqlite3.connect(sys.argv[1]) as db:\n"
        "    db.execute(\"UPDATE authority "
        "SET state='ACTIVE', version=3\")"
    )

    attacks = {
        "SQLITE MUTATION": mutation,
        "DELETION": "os.remove(sys.argv[1])",
        "REPLACEMENT": "os.replace(sys.argv[2], sys.argv[1])",
        "RENAME": "os.rename(sys.argv[1], sys.argv[1]+'.old')"
    }

    original = database.read_bytes()

    for name, action in attacks.items():
        args = [
            sys.executable, "-c",
            "import os, sys, sqlite3\n" + action,
            str(database), str(replacement)
        ]

        result = subprocess.run(
            ["/usr/bin/sandbox-exec", "-p", profile] + args,
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

        assert database.read_bytes() == original

        with sqlite3.connect(database) as db:
            assert db.execute(
                "SELECT state, version FROM authority"
            ).fetchone() == ("REVOKED", 2)

        print("PASS: " + name + " DENIED")

    subprocess.run(
        [sys.executable, "-c",
         "import sys, sqlite3\n" + mutation,
         str(database)],
        check=True,
        timeout=15
    )

    with sqlite3.connect(database) as db:
        assert db.execute(
            "SELECT state, version FROM authority"
        ).fetchone() == ("ACTIVE", 3)

    print("PASS: UNSANDBOXED POSITIVE CONTROL")
    print("PASS: OS AUTHORITY STORE ISOLATION REGRESSION")
