from dataclasses import dataclass
import hashlib
import json
from typing import Dict, List


def sha256_json(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()


@dataclass(frozen=True)
class ReplayResult:
    passed: bool
    status: str
    checks: Dict[str, bool]
    failed_checks: List[str]

    def to_dict(self):
        return {
            "passed": self.passed,
            "status": self.status,
            "checks": self.checks,
            "failed_checks": self.failed_checks,
        }


def verify_chain(
    intent_receipt,
    intent_record,
    execution,
    state_receipt,
    state_record,
    commit,
    commit_record,
    stored_state,
):
    checks = {}

    required_evidence = {
        "intent_receipt": intent_receipt,
        "intent_record": intent_record,
        "execution": execution,
        "state_receipt": state_receipt,
        "state_record": state_record,
        "commit": commit,
        "commit_record": commit_record,
        "stored_state": stored_state,
    }

    missing_evidence = [
        name
        for name, value in required_evidence.items()
        if value is None
    ]

    if missing_evidence:
        checks.update({
            f"missing_{name}": False
            for name in missing_evidence
        })

        return ReplayResult(
            passed=False,
            status="FAILED_CLOSED",
            checks=checks,
            failed_checks=[
                f"missing_{name}"
                for name in missing_evidence
            ],
        )

    # Intent Receipt signature
    intent_payload = {
        "decision_id": intent_receipt.decision_id,
        "boundary_receipt_hash":
            intent_receipt.boundary_receipt_hash,
        "status": intent_receipt.verification_status,
    }

    expected_intent_signature = sha256_json(intent_payload)

    checks["intent_receipt_signature"] = (
        intent_receipt.signature
        == expected_intent_signature
    )

    # Intent Record integrity
    intent_record_payload = {
        "decision_id": intent_record.decision_id,
        "governance_receipt_id":
            intent_record.governance_receipt_id,
        "boundary_receipt_id":
            intent_record.boundary_receipt_id,
        "intent_receipt_id":
            intent_record.intent_receipt_id,
        "status": intent_record.status,
    }

    expected_intent_hash = sha256_json(
        intent_record_payload
    )

    expected_intent_record_signature = hashlib.sha256(
        expected_intent_hash.encode()
    ).hexdigest()

    checks["intent_record_hash"] = (
        intent_record.artifact_hash
        == expected_intent_hash
    )

    checks["intent_record_signature"] = (
        intent_record.signature
        == expected_intent_record_signature
    )

    checks["intent_linkage"] = (
        intent_record.decision_id
        == intent_receipt.decision_id
        and intent_record.intent_receipt_id
        == intent_receipt.intent_receipt_id
    )

    # Execution linkage
    checks["execution_linkage"] = (
        execution.decision_id
        == intent_record.decision_id
    )

    checks["execution_status"] = (
        execution.status == "EXECUTED"
    )

    # State Receipt integrity
    expected_state_hash = sha256_json(
        state_receipt.state
    )

    expected_state_signature = hashlib.sha256(
        (
            state_receipt.execution_id
            + expected_state_hash
        ).encode()
    ).hexdigest()

    checks["state_receipt_hash"] = (
        state_receipt.state_hash
        == expected_state_hash
    )

    checks["state_receipt_signature"] = (
        state_receipt.signature
        == expected_state_signature
    )

    checks["state_receipt_linkage"] = (
        state_receipt.execution_id
        == execution.execution_id
    )

    checks["state_receipt_verified"] = (
        state_receipt.verification_status
        == "VERIFIED"
    )

    # State Record integrity
    state_record_payload = {
        "execution_id": state_record.execution_id,
        "state_receipt_id":
            state_record.state_receipt_id,
        "state_hash": state_record.state_hash,
        "verification_status":
            state_record.verification_status,
    }

    expected_state_record_hash = sha256_json(
        state_record_payload
    )

    expected_state_record_signature = hashlib.sha256(
        expected_state_record_hash.encode()
    ).hexdigest()

    checks["state_record_signature"] = (
        state_record.signature
        == expected_state_record_signature
    )

    checks["state_record_linkage"] = (
        state_record.execution_id
        == state_receipt.execution_id
        and state_record.state_receipt_id
        == state_receipt.state_receipt_id
        and state_record.state_hash
        == state_receipt.state_hash
    )

    checks["state_record_verified"] = (
        state_record.verification_status
        == "VERIFIED"
    )

    # AFS Commit integrity
    commit_payload = {
        "state_record_id":
            state_record.state_record_id,
        "execution_id":
            state_record.execution_id,
        "state_hash":
            state_record.state_hash,
        "verification_status":
            state_record.verification_status,
    }

    expected_commit_hash = sha256_json(commit_payload)

    expected_commit_signature = hashlib.sha256(
        expected_commit_hash.encode()
    ).hexdigest()

    checks["commit_hash"] = (
        commit.commit_hash
        == expected_commit_hash
    )

    checks["commit_signature"] = (
        commit.signature
        == expected_commit_signature
    )

    checks["commit_linkage"] = (
        commit.state_record_id
        == state_record.state_record_id
        and commit.execution_id
        == state_record.execution_id
    )

    checks["commit_status"] = (
        commit.committed is True
    )

    # Commit Record integrity
    commit_record_payload = {
        "commit_id": commit_record.commit_id,
        "execution_id": commit_record.execution_id,
        "commit_hash": commit_record.commit_hash,
    }

    expected_commit_record_hash = sha256_json(
        commit_record_payload
    )

    expected_commit_record_signature = hashlib.sha256(
        expected_commit_record_hash.encode()
    ).hexdigest()

    checks["commit_record_signature"] = (
        commit_record.signature
        == expected_commit_record_signature
    )

    checks["commit_record_linkage"] = (
        commit_record.commit_id
        == commit.commit_id
        and commit_record.execution_id
        == commit.execution_id
        and commit_record.commit_hash
        == commit.commit_hash
    )

    # State Store linkage
    checks["state_store_linkage"] = (
        stored_state.get("commit_id")
        == commit.commit_id
        and stored_state.get("execution_id")
        == execution.execution_id
        and stored_state.get("state_record_id")
        == state_record.state_record_id
        and stored_state.get("state_hash")
        == state_record.state_hash
    )

    checks["state_store_status"] = (
        stored_state.get("verification_status")
        == "VERIFIED"
        and stored_state.get("committed") is True
    )

    failed_checks = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    passed = len(failed_checks) == 0

    return ReplayResult(
        passed=passed,
        status="VERIFIED" if passed else "FAILED_CLOSED",
        checks=checks,
        failed_checks=failed_checks,
    )
