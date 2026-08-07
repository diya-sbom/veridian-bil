# Veridian v1.0 Demonstration

This demonstration reproduces the complete Veridian runtime governance pipeline.

---

## 1. Generate Governance Evidence

```bash
python3 demo.py
```

Expected output:

- Governance Receipt
- Boundary Receipt
- Intent Receipt
- Execution Receipt
- State Receipt
- Commit Receipt

---

## 2. Verify Receipts

```bash
python3 verify.py 1
```

Expected:

```
Verification : PASSED
```

---

## 3. PASS Replay Verification

```bash
python3 test_replay_pass.py
```

Expected:

```
status: VERIFIED
passed: True
```

All integrity checks should PASS.

---

## 4. FAIL Replay Verification

```bash
python3 test_replay_fail.py
```

Expected:

```
status: FAILED_CLOSED
passed: False
```

Tampered state should be detected automatically.

---

## Runtime Pipeline

```
Decision
    │
Governance Receipt
    │
Boundary Receipt
    │
Diya Verification
    │
Intent Receipt
    │
BIL Intent Record
    │
Executor
    │
Execution Receipt
    │
MIRA Verification
    │
State Receipt
    │
BIL State Record
    │
AFS Commit
    │
Commit Receipt
    │
BIL Commit Record
    │
State Store
    │
Replay Verifier
```

---

## Security Properties

- Governance before execution
- Verification before commit
- Immutable evidence chain
- End-to-end replay verification
- Fail-closed validation
- Tamper detection
- Deterministic verification
- Complete audit trail

---

## Veridian v1.0 Status

- ✅ Governance
- ✅ Runtime verification
- ✅ Evidence receipts
- ✅ BIL records
- ✅ Replay verification
- ✅ PASS proof
- ✅ FAIL proof
