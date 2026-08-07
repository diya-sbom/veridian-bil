from records.ledger import calculate_hash


def verify_chain(records):
    if not records:
        return True, "Empty chain"

    previous_hash = "GENESIS"

    for index, record in enumerate(records):

        if record["previous_hash"] != previous_hash:
            return False, f"Broken link at record {index}"

        expected = calculate_hash(record)

        if expected != record["current_hash"]:
            return False, f"Hash mismatch at record {index}"

        previous_hash = record["current_hash"]

    return True, "Chain verified"
