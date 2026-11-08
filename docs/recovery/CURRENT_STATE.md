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
