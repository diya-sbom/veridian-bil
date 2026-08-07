# DecisionAssure

DecisionAssure is a runtime AI governance and evidence verification engine that demonstrates how autonomous decisions can be verified before, during, and after execution.

DecisionAssure is the governance layer of the Veridian architecture.

---

# Problem

Modern AI systems can execute actions, but they rarely produce verifiable governance evidence that proves:

- what decision was made
- why it was approved
- what executed
- what state changed
- what was finally committed

DecisionAssure addresses this gap through deterministic receipts and replay verification.

---

# Architecture

Decision
│
├── Governance Receipt
│
├── Boundary Receipt
│
├── Diya Verification
│
├── Intent Receipt
│
├── BIL Intent Record
│
├── Executor
│
├── Execution Receipt
│
├── MIRA Verification
│
├── State Receipt
│
├── BIL State Record
│
├── AFS Commit
│
├── Commit Receipt
│
├── BIL Commit Record
│
└── Replay Verifier

---

# Features

- Governance receipts
- Intent receipts
- State receipts
- Commit receipts
- Boundary receipts
- Replay verification
- Tamper detection
- Fail-closed verification
- Deterministic evidence chain

---

# Validation

DecisionAssure includes:

- PASS replay verification
- FAIL replay verification
- Tamper detection
- Deterministic hashing
- Evidence linkage verification

---

# Status

Version: Veridian v1.0

Architecture: Frozen

Current focus:

- Documentation
- Demonstrations
- External validation



## Validation

Veridian includes:

- PASS replay verification
- FAIL replay verification
- Receipt integrity verification
- Record integrity verification
- Tamper detection
- Fail-closed architecture



## Documentation

- ARCHITECTURE.md
- DEMO.md
- VERIDIAN_BENCHMARK_SPEC.md

## Quick Start

```bash
python3 demo.py
python3 test_replay_pass.py
python3 test_replay_fail.py
