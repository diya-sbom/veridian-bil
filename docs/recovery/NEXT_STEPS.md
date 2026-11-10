# Veridian — Next Engineering Steps

## Recovery Checkpoint

Branch: post-v1-authority-continuation

Latest verified engineering commit:
877afc6 — Prove persistent delegation does not
survive parent revocation.

Verify live HEAD before beginning work.

## Current Priority

Complete the Recovery Pack before resuming
authority-enforcement engineering.

Do not restart or redesign the architecture.

## Engineering Objective

Prove that AI agents cannot gain or retain
consequential authority through stale approval,
capability composition, delegation chains,
persistent access, or execution-path bypasses.

All tests must preserve authorized execution
while denying unauthorized execution.

## Priority 1 — Approval-to-Execution Binding

Status: NEXT — NOT YET FULLY PROVEN

A human approval must apply to the exact action
that is eventually executed.

Adversarial tests:

1. Approved action changes before execution.
2. Approved target or resource changes.
3. Approved amount or economic limit changes.
4. Execution context materially changes.
5. Underlying authority is revoked or reduced.
6. Approval expires before execution.
7. Approval artifact is replayed or substituted.

Expected results:

- Changed execution is denied without valid
  reauthorization and fresh approval.
- Existing approval cannot expand authority.
- Executor must not perform the changed action.
- Unauthorized state commitment is blocked.
- Denial evidence is preserved.
- Independent replay reproduces the decision.
- Unchanged, valid, authorized execution
  continues to succeed.

Relevant existing commits:

0564864 — Approval enforced at execution.
fdf4446 — Independent human presence.
46eb017 — Approval does not create authority.

Inspect current implementation before editing.

## Priority 2 — Capability Composition

Status: PLANNED

Individually authorized capabilities must not
combine into a consequential action outside
the originally delegated authority.

Example:

An agent may read account information and
prepare a payment request.

Those permissions must not automatically
authorize the agent to execute payment.

Expected results:

- Evaluate effective end-to-end action.
- Deny authority expansion through composition.
- Preserve approved individual operations.
- Block unauthorized consequential execution.
- Independently reproduce the denial.

## Priority 3 — Multi-Agent Delegation

Status: PLANNED

Scenario:

Human
  |
  v
Chief-of-Staff Agent
  |
  v
Manager Agent
  |
  v
Worker Agent
  |
  v
Consequential Action

The worker must not acquire broader authority
through intermediate agent instructions.

Required checks:

- Original human authority is identifiable.
- Delegation lineage remains verifiable.
- Subdelegation stays within parent scope.
- Parent authority remains current.
- Revocation invalidates dependent authority.
- Agent instructions do not create authority.

Expected result:

Unauthorized downstream execution fails closed.

## Priority 4 — Long-Horizon Authority

Status: PLANNED

Long-running workflows must continuously
respect changes to their governing authority.

Adversarial conditions:

- Parent revocation.
- Authority contraction.
- Expiration.
- Supersession.
- Changed execution context.
- Previously installed delegated capability.

Expected results:

- Stale authority is rejected.
- Persistent capability is not treated
  as persistent authority.
- No unauthorized execution occurs.
- No unauthorized state change commits.
- The denial is independently replayable.

Existing relevant proof:

877afc6 — Persistent delegation does not
survive parent revocation.

Do not duplicate this completed scenario.
Extend only to genuinely unproven boundaries.

## Priority 5 — Independent External Validation

Status: PLANNED

A separate engineer or external operator
must be able to reproduce representative
PASS and FAIL outcomes without relying
on the original developer or ChatGPT.

Requirements:

- Documented setup instructions.
- Identifiable test commands.
- Deterministic test fixtures.
- Inspectable authority evidence.
- Inspectable execution evidence.
- Independent replay procedure.
- Recorded limitations.
- Reproducible fail-closed behavior.

Success means another operator can verify
the demonstrated enforcement boundary.

Do not claim external validation before
an external operator completes it.

## General Acceptance Criteria

For every new adversarial proof:

1. Define the legitimate authority boundary.
2. Identify the attempted authority expansion.
3. Establish a valid PASS control case.
4. Establish an unauthorized FAIL case.
5. Confirm enforcement before execution.
6. Confirm denied action does not execute.
7. Confirm unauthorized state cannot commit.
8. Preserve relevant decision evidence.
9. Reproduce the outcome through replay.
10. Document limitations and test coverage.

A test that merely reports DENY is insufficient
if the protected action still executes.

## Implementation Discipline

Review depth follows authority impact
and potential blast radius.

High-impact changes affecting Diya,
authority verification, executor behavior,
MIRA, or state commitment require
careful review and relevant regression tests.

Do not bypass existing verification gates.

Do not delete or modify .before_ safety files.

Make the smallest justified change.

Do not commit unrelated modifications.

## Session Start Procedure

Before resuming engineering:

1. Read docs/recovery/CURRENT_STATE.md.
2. Read docs/recovery/AUTHORITY_RULES.md.
3. Read docs/recovery/PROOF_INDEX.md.
4. Read this NEXT_STEPS.md.
5. Verify Git branch and current HEAD.
6. Inspect Git working-tree status.
7. Identify the exact existing implementation.
8. Run relevant baseline regression tests.
9. Implement one scoped proof at a time.
10. Update recovery documents after commit.

## Session Completion Procedure

After verified engineering work:

- Record the new commit hash.
- Record the test command and observed result.
- Update PROOF_INDEX.md.
- Update CURRENT_STATE.md.
- Update remaining priorities here.
- Preserve known limitations.
- Confirm the expected working-tree state.

## Governing Principle

Capability to reach a system does not create
authority to act on it.

History does not create authority.

Approval does not expand authority.

Every consequential action must remain
within legitimate, current, scoped authority.

## Continuation Plan — 2026-11-09

Branch: post-v1-authority-continuation
Verified engineering HEAD: d57ccee

### Completed — Do Not Repeat Without Reason
- Historical V-008 replay reproduced successfully.
- Historical evidence integrity verified.
- Tampered historical evidence rejected.
- Composed-authority denial replay corrected and passed.
- Five targeted security regression scripts passed.
- Two regression files committed at d57ccee.

### Immediate Priority
1. Review the remaining full repository regression failures.
2. Separate historical evidence compatibility from current
   authorization requirements.
3. Preserve mandatory verified_action enforcement.
4. Never allow legacy replay rules into live execution.
5. Run affected security regressions after any correction.

### Next Engineering Phase
- Validate current authority at execution time.
- Expand adversarial coverage for authority composition.
- Verify delegation lineage and parent revocation.
- Prepare reproducible proof for an external operator.

These are continuing objectives, not claims that earlier
related proofs are incomplete.

### Security Review Discipline
Before modifying security-sensitive code:
- Inspect existing authorization safeguards.
- Inspect trusted provenance and fail-closed paths.
- Review relevant secure examples and negative tests.
- Evaluate blast radius before changes.
- Do not assume an AI coding agent retrieved every safeguard.

### Completion Requirements
- Record exact test results and limitations.
- Update Recovery Pack after verified changes.
- Commit only scoped, reviewed files.
- Preserve all existing .before_ safety backups.
