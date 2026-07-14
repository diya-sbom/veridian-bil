from database import get_connection


def audit_log():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               timestamp,
               agent,
               action,
               decision
        FROM receipts
        ORDER BY timestamp ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    print("\nDecisionAssure Audit Log")
    print("=" * 70)

    if not rows:
        print("No audit records found.")
        return

    for row in rows:
        rid, timestamp, agent, action, decision = row

        print(f"Receipt ID : {rid}")
        print(f"Timestamp  : {timestamp}")
        print(f"Agent      : {agent}")
        print(f"Action     : {action}")
        print(f"Decision   : {decision}")
        print("-" * 70)


if __name__ == "__main__":
    audit_log()
