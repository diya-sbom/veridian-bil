# Veridian Quick Start

This guide demonstrates the complete Veridian runtime governance workflow in a few minutes.

---

## Clone

```bash
git clone https://github.com/diya-sbom/DecisionAssure.git
cd DecisionAssure
```

---

## Run the Demo

```bash
python3 demo.py
```

This creates:

- Governance Receipt
- Boundary Receipt
- Intent Receipt
- BIL Intent Record

---

## Execute

```bash
python3 test_executor.py
```

---

## Verify State

```bash
python3 test_state_receipt.py
```

---

## Commit

```bash
python3 test_commit.py
```

---

## Replay Verification (PASS)

```bash
python3 test_replay_pass.py
```

Expected:

```
PASSED : True
STATUS : VERIFIED
```

---

## Replay Verification (FAIL)

```bash
python3 test_replay_fail.py
```

Expected:

```
PASSED : False
STATUS : FAILED_CLOSED
```

---

## Project Structure

```
README.md
ARCHITECTURE.md
DEMO.md
QUICKSTART.md
VERIDIAN_BENCHMARK_SPEC.md
replay_verifier.py
demo.py
```

---

## Security Properties

- Governance before execution
- Verification before commit
- Immutable evidence chain
- Replayable verification
- Tamper detection
- Fail-closed execution
- End-to-end traceability
