from datetime import datetime

from records.ledger import link_record


def create_commit_record(
    record_id,
    payload,
    previous_hash,
):
    record = {
        "record_id": record_id,
        "record_type": "COMMIT",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": payload,
    }

    return link_record(record, previous_hash)
