import sqlite3

DB_NAME = "receipts.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Receipts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        agent TEXT,
        action TEXT,
        decision TEXT,
        receipt_hash TEXT
    )
    """)

    # Responsibilities table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS responsibilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        agent TEXT,
        responsibility TEXT,
        owner TEXT,
        status TEXT,
        receipt_hash TEXT
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":

    initialize_database()

    conn = get_connection()
    cursor = conn.cursor()

    print("\n===== RECEIPTS =====")
    cursor.execute("SELECT * FROM receipts")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    print("\n===== RESPONSIBILITIES =====")
    cursor.execute("SELECT * FROM responsibilities")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    conn.close()
