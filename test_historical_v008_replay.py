"""Historical V-008 replay. Never used for live authorization."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

COMMIT = "542b6e7"
VERIFIER_PATH = "replay_verifier.py"
TEST_PATH = "test_replay_cross_process_consumer.py"


def git_blob(path):
    return subprocess.check_output(
        ["git", "show", f"{COMMIT}:{path}"]
    )


def main():
    historical_verifier = git_blob(VERIFIER_PATH)
    current_test = git_blob(TEST_PATH).decode("utf-8")

    expected_bundle = git_blob(
        "validation/v008_evidence_bundle.json"
    )
    actual_bundle = Path(
        "validation/v008_evidence_bundle.json"
    ).read_bytes()

    if actual_bundle != expected_bundle:
        raise SystemExit("FAIL: Historical evidence differs from Git")

    with tempfile.TemporaryDirectory() as directory:
        verifier = Path(directory) / "replay_verifier.py"
        verifier.write_bytes(historical_verifier)

        command = (
            "import sys; "
            "sys.path.insert(0, sys.argv[1]); "
            "exec(compile(sys.stdin.read(), "
            "'historical_v008_test', 'exec'))"
        )

        result = subprocess.run(
            [sys.executable, "-c", command, directory],
            input=current_test,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise SystemExit(
                "FAIL: Historical V-008 replay verification"
            )


    # Negative proof: modified historical evidence must fail.
    with tempfile.TemporaryDirectory() as directory:
        verifier = Path(directory) / "replay_verifier.py"
        verifier.write_bytes(historical_verifier)

        bundle = json.loads(actual_bundle)
        bundle["intent_receipt"]["decision_id"] = "TAMPERED-DECISION"

        tampered_path = Path(directory) / "tampered.json"
        tampered_path.write_text(json.dumps(bundle))

        tampered_test = current_test.replace(
            "validation/v008_evidence_bundle.json",
            str(tampered_path),
        )

        if tampered_test == current_test:
            raise SystemExit("FAIL: Evidence path not found")

        result = subprocess.run(
            [sys.executable, "-c", command, directory],
            input=tampered_test,
            text=True,
            capture_output=True,
        )

        if result.returncode == 0:
            raise SystemExit("FAIL: Tampered evidence accepted")

        if "intent_receipt_signature: FAIL" not in result.stdout:
            raise SystemExit("FAIL: Expected rejection not observed")

    print("PASS: TAMPERED HISTORICAL EVIDENCE REJECTED")

    print("PASS: HISTORICAL V-008 REPLAY")
    print("PASS: ORIGINAL EVIDENCE PRESERVED")
    print("PASS: CURRENT VERIFIER UNCHANGED")


if __name__ == "__main__":
    main()
