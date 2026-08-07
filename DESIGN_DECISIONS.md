# Veridian Design Decisions

This document records the evolution of the Veridian architecture.

Its purpose is to preserve the reasoning behind every major architectural decision and provide a chronological record of independent development.

---

# DD-001

Date:
2026

Decision:
Create Veridian as a runtime governance platform rather than another AI model.

Reason:

Large language models continue becoming more capable, but capability alone does not provide governance, evidence, or accountability.

The objective of Veridian is to provide a runtime control layer independent of the underlying model.

Status:

Accepted

---

# DD-002

Decision:

Separate governance from execution.

Reason:

Policy decisions should not be mixed with runtime execution.

Governance determines authorization.

Execution performs actions.

Verification proves the outcome.

Status:

Accepted

---

# DD-003

Decision:

Introduce DecisionAssure.

Reason:

Governance decisions require deterministic evidence before execution begins.

DecisionAssure records responsibility, accountability, admissibility, and policy decisions.

Status:

Accepted

---

# DD-004

Decision:

Introduce Diya.

Reason:

Intent must be verified before execution.

Execution without verified intent creates governance risk.

Status:

Accepted

---

# DD-005

Decision:

Introduce MIRA.

Reason:

Execution success does not guarantee correct system state.

Post-execution verification is required before state can be trusted.

Status:

Accepted

---

# DD-006

Decision:

Introduce AFS.

Reason:

Verified state must not automatically become committed state.

AFS becomes the final commit authority.

Status:

Accepted

---

# DD-007

Decision:

Introduce BIL.

Reason:

Evidence must be immutable.

Intent, State, and Commit become permanent evidence records.

Status:

Accepted

---

# DD-008

Decision:

Introduce Boundary Receipts.

Reason:

Every trust boundary should generate verifiable evidence.

Each subsystem handoff becomes independently verifiable.

Status:

Accepted

---

# DD-009

Decision:

Introduce Replay Verification.

Reason:

Evidence should not simply exist.

Independent parties must be able to replay the entire governance chain and reproduce verification.

Status:

Accepted

---

# DD-010

Decision:

Freeze Veridian v1.0.

Reason:

The architecture now demonstrates governance, execution, evidence, persistence, replay verification, PASS validation, and FAIL-CLOSED validation.

Future work will prioritize documentation, packaging, validation, and adoption rather than expanding the core architecture.

Status:

Frozen
