from continuity.ledger import link
from continuity.verify import verify_chain

records = []

previous_hash = "GENESIS"

for record_type in ["INTENT", "STATE", "COMMIT"]:

    payload = {
        "step": record_type
    }

    record = {
        "record_id": record_type.lower(),
        "record_type": record_type,
        "timestamp": "2026-01-01T00:00:00Z",
        "payload": payload,
    }

    linked = link(previous_hash, record)

    records.append(linked)

    previous_hash = linked["current_hash"]

print(f"Records created: {len(records)}")

# Verify original chain
result = verify_chain(records)
print(result)

# Tamper with the STATE record
records[1]["payload"]["step"] = "HACKED"

# Verify again
result = verify_chain(records)
print(result)
