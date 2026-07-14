from database import get_connection


def list_receipts():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               timestamp,
               agent,
               action,
               decision
        FROM receipts
        ORDER BY id
    """)

    rows = cursor.fetchall()

    conn.close()

    if not rows:
        print("No receipts found.")
        return

    print("\nDecisionAssure Receipt Inventory")
    print("=" * 70)

    for row in rows:
        rid, ts, agent, action, decision = row

        print(f"""
Receipt ID : {rid}
Timestamp  : {ts}
Agent      : {agent}
Action     : {action}
Decision   : {decision}
----------------------------------------
""")

if __name__ == "__main__":
    list_receipts()
