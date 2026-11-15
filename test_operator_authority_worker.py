"""Test-only operator-configured authority worker. No payments."""
import json
import os
import subprocess
import sys

worker = r'''
import contextlib
import io
import json
import os
import runpy
import sys

from executor.guarded_execution import execute_with_current_authority

request = json.loads(sys.stdin.read())

with contextlib.redirect_stdout(io.StringIO()):
    f = runpy.run_path("test_guarded_execution_revocation.py")

mode = os.environ.get("VERIDIAN_TEST_AUTHORITY_MODE")

states = {
    "ACTIVE": ("active_state", "active_state_boundary"),
    "REVOKED": ("revoked_state", "revoked_state_boundary"),
}

result = {"status": "FAILED_CLOSED"}

if mode in states and isinstance(request, dict):
    state_key, boundary_key = states[mode]
    decision = f["payment"]

    if (
        request.get("action") == decision.intended_action
        and request.get("payee") == decision.governed_resource
        and type(request.get("amount")) is int
        and request["amount"] == decision.requested_authority_units
    ):
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

        if (
            verification.status == "VERIFIED"
            and verification.verified_action == "EXECUTE_PAYMENT"
            and record.status == "VERIFIED"
            and record.verified_action == "EXECUTE_PAYMENT"
            and execution.status == "EXECUTED"
            and execution.action == "EXECUTE_PAYMENT"
        ):
            result["status"] = "VERIFIED"

print(json.dumps(result))
'''

def check(mode, request):
    env = os.environ.copy()
    env.pop("VERIDIAN_TEST_AUTHORITY_MODE", None)
    if mode is not None:
        env["VERIDIAN_TEST_AUTHORITY_MODE"] = mode

    process = subprocess.run(
        [sys.executable, "-c", worker],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=True,
    )
    return json.loads(process.stdout)

request = {
    "action": "EXECUTE_PAYMENT",
    "payee": "payee-A",
    "amount": 500,
}

assert check("ACTIVE", request)["status"] == "VERIFIED"
print("PASS: OPERATOR-CONFIGURED ACTIVE AUTHORITY VERIFIED")

forged = dict(request)
forged["test_operator_mode"] = "ACTIVE"
forged["authority_state"] = "ACTIVE"

assert check("REVOKED", forged)["status"] == "FAILED_CLOSED"
print("PASS: REQUEST CANNOT OVERRIDE REVOKED AUTHORITY")

assert check(None, forged)["status"] == "FAILED_CLOSED"
print("PASS: MISSING AUTHORITY CONFIGURATION FAILS CLOSED")

changed = dict(request)
changed["amount"] = 1000

assert check("ACTIVE", changed)["status"] == "FAILED_CLOSED"
print("PASS: PAYMENT AMOUNT CHANGE REJECTED")

print("PASS: OPERATOR-CONFIGURED AUTHORITY WORKER REGRESSION")
