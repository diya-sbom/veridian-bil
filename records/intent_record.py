from datetime import datetime

from records.ledger import link_record


def create_intent_record(
    record_id,
    payload,
    previous_hash="GENESIS",
):
    record = {
        "record_id": record_id,
        "record_type": "INTENT",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": payload,
    }

    return link_record(record, previous_hash)
