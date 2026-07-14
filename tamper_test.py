from database import get_connection
from receipts import generate_receipt


def tamper_test():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               agent,
               action,
               decision,
               receipt_hash
        FROM receipts
        ORDER BY id DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    if row is None:
        print("No receipts found.")
        return

    receipt_id, agent, action, decision, stored_hash = row

    print("\nDecisionAssure Tamper Test")
    print("=" * 50)

    tests = [

        ("Original", agent, action, decision),

        ("Decision Changed",
         agent,
         action,
         "REJECTED"),

        ("Action Changed",
         agent,
         "Delete Flight",
         decision),

        ("Agent Changed",
         "MaliciousAgent",
         action,
         decision)

    ]

    passed = 0
    failed = 0

    for name, a, act, dec in tests:

        new_hash = generate_receipt(a, act, dec)

        print(f"\n{name}")
        print("-" * 40)

        print("Stored :", stored_hash)
        print("New    :", new_hash)

        if stored_hash == new_hash:
            print("Result : PASS")
            passed += 1
        else:
            print("Result : FAIL (Tampering Detected)")
            failed += 1

    print("\nSummary")
    print("=" * 50)
    print(f"Tests Run          : {len(tests)}")
    print(f"Passed             : {passed}")
    print(f"Tampering Detected : {failed}")


if __name__ == "__main__":
    tamper_test()
