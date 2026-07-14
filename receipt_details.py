from database import get_connection
import sys


def show_receipt(receipt_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               timestamp,
               agent,
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
        return

    rid, ts, agent, action, decision, receipt_hash = row

    print("\nDecisionAssure Receipt")
    print("=" * 50)

    print(f"Receipt ID : {rid}")
    print(f"Timestamp  : {ts}")
    print(f"Agent      : {agent}")
    print(f"Action     : {action}")
    print(f"Decision   : {decision}")

    print("\nReceipt Hash")
    print(receipt_hash)


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python3 receipt_details.py <receipt_id>")
        sys.exit()

    show_receipt(int(sys.argv[1]))
