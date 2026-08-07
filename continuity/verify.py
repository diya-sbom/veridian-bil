from continuity.ledger import calculate_hash
from continuity.models import VerificationResult


def verify_chain(records):
    """
    Verify an ordered BIL continuity chain.
    """
    previous_hash = "GENESIS"

    for record in records:
        expected = calculate_hash({
            "record_id": record["record_id"],
            "record_type": record["record_type"],
            "timestamp": record["timestamp"],
            "payload": record["payload"],
            "previous_hash": previous_hash,
        })

        if record["previous_hash"] != previous_hash:
            return VerificationResult(
                passed=False,
                message="Broken previous hash",
                failed_record=record["record_id"],
            )

        if record["current_hash"] != expected:
            return VerificationResult(
                passed=False,
                message="Hash mismatch",
                failed_record=record["record_id"],
            )

        previous_hash = record["current_hash"]

    return VerificationResult(
        passed=True,
        message="Continuity verified",
        failed_record=""
    )
