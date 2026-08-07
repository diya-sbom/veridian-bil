import hashlib
import json


def calculate_hash(record: dict) -> str:
    """Create a deterministic SHA-256 hash of a record."""
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def link(previous_hash: str, record: dict):
    """Link a record to the previous one."""
    payload = dict(record)
    payload["previous_hash"] = previous_hash
    payload["current_hash"] = calculate_hash(payload)
    return payload
