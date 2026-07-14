from database import get_connection
from receipts import generate_receipt


def verify_receipt(receipt_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT agent,
               action,
               decision,
               receipt_hash
        FROM receipts
        WHERE id = ?
    """, (receipt_id,))

    row = cursor.fetchone()

    conn.close()

    if row is None:
        print(f"Receipt ID {receipt_id} not found.")
        return False

    agent, action, decision, stored_hash = row

    computed_hash = generate_receipt(
        agent,
        action,
        decision
    )

    print("\nDecisionAssure Verification")
    print("=" * 40)

    print(f"Receipt ID : {receipt_id}")
    print(f"Agent      : {agent}")
    print(f"Action     : {action}")
    print(f"Decision   : {decision}")

    print("\nStored Hash")
    print(stored_hash)

    print("\nComputed Hash")
    print(computed_hash)

    if stored_hash == computed_hash:
        print("\nVerification : PASSED")
        return True
    else:
        print("\nVerification : FAILED")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 verify.py <receipt_id>")
    else:
        verify_receipt(int(sys.argv[1]))
