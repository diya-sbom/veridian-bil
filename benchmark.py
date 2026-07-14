import time

from app import store_decision
from verify import verify_receipt


TOTAL = 1000


def run_benchmark():

    print("\nDecisionAssure Benchmark v1")
    print("=" * 40)

    start = time.perf_counter()

    for i in range(TOTAL):
        store_decision(
            "TravelAgent",
            f"Book Flight {i}",
            "APPROVED"
        )

    insert_time = time.perf_counter() - start

    start = time.perf_counter()

    passed = 0

    for receipt_id in range(1, TOTAL + 1):
        if verify_receipt(receipt_id):
            passed += 1

    verify_time = time.perf_counter() - start

    print(f"\nTotal Decisions     : {TOTAL}")
    print(f"Verified            : {passed}")
    print(f"Insert Time         : {insert_time:.3f} sec")
    print(f"Verify Time         : {verify_time:.3f} sec")
    print(f"Insert Avg          : {(insert_time/TOTAL)*1000:.3f} ms")
    print(f"Verify Avg          : {(verify_time/TOTAL)*1000:.3f} ms")


if __name__ == "__main__":
    run_benchmark()
