import hashlib
import json
from typing import Any, Dict


GENESIS_HASH = "GENESIS"


def canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def calculate_hash(record: Dict[str, Any]) -> str:
    protected_record = {
        key: value
        for key, value in record.items()
        if key != "current_hash"
    }

    encoded = canonical_json(protected_record).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def link_record(
    record: Dict[str, Any],
    previous_hash: str = GENESIS_HASH,
) -> Dict[str, Any]:
    linked_record = dict(record)
    linked_record["previous_hash"] = previous_hash
    linked_record["current_hash"] = calculate_hash(linked_record)
    return linked_record
