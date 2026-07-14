from fastapi import FastAPI, HTTPException, Query
from app import store_decision
from database import get_connection
from receipts import generate_receipt

app = FastAPI(
    title="DecisionAssure API",
    version="0.2.0",
    description=(
        "Decision governance, cryptographic receipts, verification, "
        "audit history, and responsibility ownership."
    ),
)


@app.get("/")
def home():
    return {
        "service": "DecisionAssure",
        "version": "0.2.0",
        "status": "running",
    }


@app.post("/decision")
def create_decision(
    agent: str,
    action: str,
    decision: str,
):
    normalized_decision = decision.strip().upper()

    allowed_decisions = {
        "APPROVED",
        "REJECTED",
        "REQUIRE_REVIEW",
    }

    if normalized_decision not in allowed_decisions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Decision must be APPROVED, REJECTED, "
                "or REQUIRE_REVIEW."
            ),
        )

    receipt = store_decision(
        agent.strip(),
        action.strip(),
        normalized_decision,
    )

    return {
        "status": "stored",
        "agent": agent.strip(),
        "action": action.strip(),
        "decision": normalized_decision,
        "receipt": receipt,
    }


@app.get("/receipt/{receipt_id}")
def get_receipt(receipt_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            timestamp,
            agent,
            action,
            decision,
            receipt_hash
        FROM receipts
        WHERE id = ?
        """,
        (receipt_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found.",
        )

    return {
        "id": row[0],
        "timestamp": row[1],
        "agent": row[2],
        "action": row[3],
        "decision": row[4],
        "receipt": row[5],
    }


@app.get("/verify/{receipt_id}")
def verify_receipt(receipt_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            agent,
            action,
            decision,
            receipt_hash
        FROM receipts
        WHERE id = ?
        """,
        (receipt_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found.",
        )

    agent, action, decision, stored_hash = row

    computed_hash = generate_receipt(
        agent,
        action,
        decision,
    )

    verified = stored_hash == computed_hash

    return {
        "receipt_id": receipt_id,
        "verified": verified,
        "stored_hash": stored_hash,
        "computed_hash": computed_hash,
        "result": "PASSED" if verified else "FAILED",
    }


@app.get("/audit")
def audit(
    limit: int = Query(default=25, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            timestamp,
            agent,
            action,
            decision,
            receipt_hash
        FROM receipts
        ORDER BY id DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "agent": row[2],
            "action": row[3],
            "decision": row[4],
            "receipt": row[5],
        }
        for row in rows
    ]


@app.get("/agent/{agent}")
def get_agent(
    agent: str,
    limit: int = Query(default=100, ge=1, le=500),
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            timestamp,
            action,
            decision,
            receipt_hash
        FROM receipts
        WHERE agent = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (agent, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "action": row[2],
            "decision": row[3],
            "receipt": row[4],
        }
        for row in rows
    ]


@app.get("/decision/{decision_status}")
def get_decision(
    decision_status: str,
    limit: int = Query(default=100, ge=1, le=500),
):
    normalized_decision = decision_status.strip().upper()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            timestamp,
            agent,
            action,
            receipt_hash
        FROM receipts
        WHERE decision = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (normalized_decision, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "agent": row[2],
            "action": row[3],
            "decision": normalized_decision,
            "receipt": row[4],
        }
        for row in rows
    ]


@app.get("/stats")
def stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM receipts")
    total_decisions = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(DISTINCT agent) FROM receipts"
    )
    unique_agents = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(DISTINCT action) FROM receipts"
    )
    unique_actions = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT decision, COUNT(*)
        FROM receipts
        GROUP BY decision
        ORDER BY decision
        """
    )
    decisions = dict(cursor.fetchall())

    cursor.execute(
        "SELECT COUNT(*) FROM responsibilities"
    )
    total_responsibilities = cursor.fetchone()[0]

    conn.close()

    return {
        "total_decisions": total_decisions,
        "unique_agents": unique_agents,
        "unique_actions": unique_actions,
        "decision_counts": decisions,
        "total_responsibilities": total_responsibilities,
    }


@app.post("/responsibility")
def create_responsibility(
    agent: str,
    responsibility: str,
    owner: str,
    status: str = "ACTIVE",
):
    clean_agent = agent.strip()
    clean_responsibility = responsibility.strip()
    clean_owner = owner.strip()
    clean_status = status.strip().upper()

    allowed_statuses = {
        "ACTIVE",
        "SUSPENDED",
        "REVOKED",
        "TRANSFERRED",
    }

    if not clean_agent:
        raise HTTPException(
            status_code=400,
            detail="Agent cannot be empty.",
        )

    if not clean_responsibility:
        raise HTTPException(
            status_code=400,
            detail="Responsibility cannot be empty.",
        )

    if not clean_owner:
        raise HTTPException(
            status_code=400,
            detail="Owner cannot be empty.",
        )

    if clean_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=(
                "Status must be ACTIVE, SUSPENDED, "
                "REVOKED, or TRANSFERRED."
            ),
        )

    receipt_hash = generate_receipt(
        clean_agent,
        clean_responsibility,
        clean_status,
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO responsibilities (
            timestamp,
            agent,
            responsibility,
            owner,
            status,
            receipt_hash
        )
        VALUES (
            datetime('now'),
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            clean_agent,
            clean_responsibility,
            clean_owner,
            clean_status,
            receipt_hash,
        ),
    )

    responsibility_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "status": "stored",
        "responsibility_id": responsibility_id,
        "agent": clean_agent,
        "responsibility": clean_responsibility,
        "owner": clean_owner,
        "responsibility_status": clean_status,
        "receipt": receipt_hash,
    }


@app.get("/responsibility/id/{responsibility_id}")
def get_responsibility_by_id(
    responsibility_id: int,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            timestamp,
            agent,
            responsibility,
            owner,
            status,
            receipt_hash
        FROM responsibilities
        WHERE id = ?
        """,
        (responsibility_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Responsibility record not found.",
        )

    return {
        "id": row[0],
        "timestamp": row[1],
        "agent": row[2],
        "responsibility": row[3],
        "owner": row[4],
        "status": row[5],
        "receipt": row[6],
    }


@app.get("/responsibility/agent/{agent}")
def get_responsibilities_by_agent(agent: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            timestamp,
            agent,
            responsibility,
            owner,
            status,
            receipt_hash
        FROM responsibilities
        WHERE agent = ?
        ORDER BY id DESC
        """,
        (agent,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "agent": row[2],
            "responsibility": row[3],
            "owner": row[4],
            "status": row[5],
            "receipt": row[6],
        }
        for row in rows
    ]


@app.get("/owner/{owner}")
def get_responsibilities_by_owner(owner: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            timestamp,
            agent,
            responsibility,
            owner,
            status,
            receipt_hash
        FROM responsibilities
        WHERE owner = ?
        ORDER BY id DESC
        """,
        (owner,),
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "agent": row[2],
            "responsibility": row[3],
            "owner": row[4],
            "status": row[5],
            "receipt": row[6],
        }
        for row in rows
    ]


@app.get("/responsibility-stats")
def responsibility_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM responsibilities"
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT status, COUNT(*)
        FROM responsibilities
        GROUP BY status
        ORDER BY status
        """
    )
    status_counts = dict(cursor.fetchall())

    cursor.execute(
        """
        SELECT COUNT(DISTINCT owner)
        FROM responsibilities
        """
    )
    unique_owners = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(DISTINCT agent)
        FROM responsibilities
        """
    )
    governed_agents = cursor.fetchone()[0]

    conn.close()

    return {
        "total_responsibilities": total,
        "unique_owners": unique_owners,
        "governed_agents": governed_agents,
        "status_counts": status_counts,
    }
