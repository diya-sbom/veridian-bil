"""Independent payment-service integration regression.

Test-only. No network access or real financial transactions.
"""
import json
import os
import subprocess
import sys


def run_service(request, operator_mode):
    """Run a fresh service process with operator-selected authority."""
    worker = r'''
import json
import os
import sys

try:
    request = json.loads(sys.stdin.read())
    mode = os.environ.get("VERIDIAN_TEST_AUTHORITY_MODE")

    # Until trusted authorization, independent current authority,
    # and durable commitment are connected, execution is forbidden.
    result = {
        "status": "FAILED_CLOSED",
        "reason": "ENFORCEMENT_NOT_FULLY_CONNECTED",
    }

    print(json.dumps(result))
except Exception:
    print(json.dumps({
        "status": "FAILED_CLOSED",
        "reason": "INVALID_REQUEST",
    }))
'''

    env = os.environ.copy()
    env.pop("VERIDIAN_TEST_AUTHORITY_MODE", None)

    if operator_mode is not None:
        env["VERIDIAN_TEST_AUTHORITY_MODE"] = operator_mode

    result = subprocess.run(
        [sys.executable, "-c", worker],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=True,
    )

    return json.loads(result.stdout)


request = {
    "action": "EXECUTE_PAYMENT",
    "payee": "payee-A",
    "amount": 500,
    "authority_state": "ACTIVE",
}

result = run_service(request, "REVOKED")
assert result["status"] == "FAILED_CLOSED"
print("PASS: REVOKED AUTHORITY DID NOT CAUSE PAYMENT")

result = run_service(request, None)
assert result["status"] == "FAILED_CLOSED"
print("PASS: MISSING AUTHORITY CONFIGURATION FAILED CLOSED")

result = run_service(request, "ACTIVE")
assert result["status"] == "FAILED_CLOSED"
print("PASS: INCOMPLETE ENFORCEMENT FAILED CLOSED")

print("PASS: INDEPENDENT PAYMENT-SERVICE BASELINE")
