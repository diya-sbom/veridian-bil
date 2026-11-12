# Veridian — Current State

## Repository
Path: ~/Desktop/APEX/decisionassure/veridian-bil
Branch: post-v1-authority-continuation

## Latest Verified Checkpoint
Commit: 877afc6
Title: Prove persistent delegation does not survive parent revocation

Previous commit:
0564864 — Enforce independent human approval at execution

## Purpose
Veridian enforces whether an AI agent has legitimate,
current, scoped authority to perform a consequential
action and whether resulting state changes are admissible.

## Architecture
Decision
→ Governance Receipt
→ Diya Verification
→ Intent Record
→ Executor
→ MIRA Verification
→ State Record
→ AFS Commit
→ BIL Commit Record
→ State Store
→ Replay Verification

Source: ARCHITECTURE.md

## Established Security Principles
- Capability does not create authority.
- Authority must be verified before execution.
- Human approval does not independently create authority.
- Human approval must be independently verified and
  valid at execution time.
- Parent revocation invalidates dependent delegation.
- Revoked, expired, or out-of-scope authority fails closed.
- Authority decisions must be independently replayable.
- Tampered evidence must fail closed.

## Latest Engineering Result
Persistent-delegation regression tests were reported
as passing before commit 877afc6.

The commit contains changes to:
- decisionassure/decision_replay.py
- test_compromised_application_identity_persistent_derived_authority.py

## Next Engineering Objective
Prove that human approval becomes invalid when the
approved action, target, amount, context, authority
state, or timing changes before execution.

## Recovery Pack
Location: docs/recovery/

Planned documents:
- CURRENT_STATE.md
- ARCHITECTURE.md
- AUTHORITY_RULES.md
- PROOF_INDEX.md
- NEXT_STEPS.md
- ACQUISITION_READINESS.md
- CHAT_RECOVERY.md

## Verification Rule
Git history, source code, executable tests, and proof
artifacts are authoritative.

Do not treat chat history as implementation evidence.

Before continuing engineering:
1. Verify current branch and HEAD.
2. Inspect git status.
3. Read existing architecture and authority documents.
4. Run the relevant regression tests.
5. Make only necessary, scoped changes.
6. Commit only after verification.

## Notes
SPEC.md was observed empty on November 7, 2026.
Existing .before_ safety backups must remain untouched.

This document is a historical recovery checkpoint.
Always verify live repository state before relying on it.

## Continuation Checkpoint — 2026-11-09

Branch: post-v1-authority-continuation
HEAD: d57ccee
Commit: Preserve historical V-008 replay and trusted authority validation
Previous checkpoint: 5042098

### Completed
- Historical V-008 cross-process replay: PASS
- Original historical evidence preserved: PASS
- Historical evidence tampering rejected: PASS
- Composed-authority denial replay: PASS
- Independent human approval regression: PASS
- Execution-time revocation regression: PASS
- Approval-to-decision binding regression: PASS
- Five targeted security regression scripts: PASS

### Security Boundaries
- Current production verifier remains unchanged.
- Current verified_action enforcement remains mandatory.
- Historical verification is isolated from live authorization.
- Historical V-008 verifier originates from commit 542b6e7.

### Remaining
- Full repository regression suite not yet confirmed clean.
- Resolve legacy cross-process test compatibility without weakening current verification.
- Update PROOF_INDEX.md and NEXT_STEPS.md.
- Preserve existing .before_ safety backups.

### Next Engineering Action
Update Recovery Pack proof index and next steps.
Then investigate remaining regression compatibility.

## Verified Continuation Checkpoint - 2026-11-10

Branch: post-v1-authority-continuation
Engineering HEAD: a75d618

### Completed
- Generated V-008 evidence isolated from preserved historical evidence: PASS.
- Cross-resource delegated authority denial replay: PASS.
- End-to-end fixture now supplies authenticated Ed25519 execution evidence: PASS.
- State receipt verification: PASS.
- State record verification: PASS.
- State commitment and stored-state verification: PASS.
- Historical V-008 replay and tamper rejection: PASS.
- Original historical evidence unchanged: PASS.
- All 73 root-level regression scripts completed successfully.
- Post-regression tracked working tree verified clean.

### Security Boundaries
- Production authorization and replay verification controls unchanged.
- Execution success alone does not establish authenticated execution.
- Invalid or missing authenticated evidence must fail closed.
- Historical V-008 evidence must not be regenerated in place.
- Existing .before_ safety backups must remain untouched.

### Remaining
- Nested and external integration verification remains separate.
- Prepare reproducible independent operator validation.
- Update PROOF_INDEX.md and NEXT_STEPS.md.
- Preserve this engineering checkpoint before further changes.

## Verified Engineering Checkpoint - 2026-11-11

Branch: post-v1-authority-continuation
Engineering HEAD: 0014d09

- Isolated two-process cryptographic trust regression committed.
- All 74 root-level regression scripts passed.
- Post-regression tracked repository integrity verified.
- Historical V-008 evidence remained unchanged.
- Independent third-party trust approval and execution-time
  authority reproduction remain pending.
