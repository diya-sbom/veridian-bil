from database import initialize_database, get_connection
from receipts import generate_receipt
from datetime import datetime, UTC


def store_decision(agent, action, decision):

    initialize_database()

    receipt_hash = generate_receipt(agent, action, decision)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO receipts
        (timestamp, agent, action, decision, receipt_hash)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now(UTC).isoformat(),
        agent,
        action,
        decision,
        receipt_hash
    ))

    conn.commit()
    conn.close()

    print("\nDecision Stored Successfully\n")
    print("Agent      :", agent)
    print("Action     :", action)
    print("Decision   :", decision)
    print("Receipt    :", receipt_hash)

    return receipt_hash


if __name__ == "__main__":

    store_decision(
        "TravelAgent",
        "Book Flight",
        "APPROVED"
    )
