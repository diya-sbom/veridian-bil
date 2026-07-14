import hashlib
import json


def generate_receipt(agent, action, decision):
    payload = {
        "agent": agent,
        "action": action,
        "decision": decision
    }

    receipt = json.dumps(payload, sort_keys=True)
    receipt_hash = hashlib.sha256(receipt.encode()).hexdigest()
    return receipt_hash


def verify_receipt(agent, action, decision, stored_hash):
    new_hash = generate_receipt(agent, action, decision)
    return new_hash == stored_hash


if __name__ == "__main__":

    # Simulate a changed decision (tampering)
    agent = "TravelAgent"
    action = "Book Flight"
    decision = "REJECTED"

    # Original hash stored when decision was APPROVED
    stored_hash = "2c6dfcd343f4a5c2224d7e429a3cde80afc03541a269b808a831237d13ac619a"

    print("Stored Hash:")
    print(stored_hash)

    new_hash = generate_receipt(agent, action, decision)

    print("\nNew Hash:")
    print(new_hash)

    if verify_receipt(agent, action, decision, stored_hash):
        print("\nReceipt Verification: PASSED")
    else:
        print("\nReceipt Verification: FAILED")
