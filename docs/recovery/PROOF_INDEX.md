# Veridian — Proof Index

## Purpose

This document connects Veridian security claims
to Git commits, executable tests, and evidence.

The repository is the source of truth.
A commit title alone does not prove a security claim.

## Repository Checkpoint

Branch: post-v1-authority-continuation

Latest verified HEAD:
877afc6 — Prove persistent delegation does not
survive parent revocation.

Checkpoint date: November 7, 2026.

This is a historical checkpoint.
Always verify the current Git HEAD.

## Proof Status Definitions

REPRODUCED:
The relevant test was executed and its expected
results were observed.

COMMITTED:
The commit was confirmed in Git history, but
its complete test evidence has not been
reproduced during this recovery session.

PLANNED:
The security requirement is identified, but
the required adversarial proof remains pending.

A passing local test is not automatically
equivalent to independent external validation.

## P01 — Persistent Delegation Revocation

Commit: 877afc6
Status: REPRODUCED

Claim:
A previously issued delegated execution path
must not survive revocation of parent authority.

Implementation:
decisionassure/decision_replay.py

Regression test:
test_compromised_application_identity_persistent_derived_authority.py

Reproduction command:
python3 test_compromised_application_identity_persistent_derived_authority.py

Observed results:
- Valid delegation remained bounded.
- Missing trusted parent evidence was denied.
- Revoked parent authority caused denial.
- Persistent capability did not create
  persistent authority.
- Denial was independently replayed.
- Unauthorized state change was blocked.

Result:
PASS, observed November 7, 2026.

Scope:
This proves the tested scenario, not every
possible persistent-delegation attack.

## P02 — Human Approval at Execution

Commit: 0564864
Status: COMMITTED

Claim:
Independent human approval must be enforced
in the live execution path.

Required verification:
Inspect guarded execution implementation,
regression tests, and execution evidence.

## P03 — Independent Approval Provenance

Commit: fdf4446
Status: COMMITTED

Claim:
Trusted human approval requires independently
established human presence and provenance.

Required verification:
Reproduce valid and invalid provenance cases.

## P04 — Approval Does Not Create Authority

Commit: 46eb017
Status: COMMITTED

Claim:
A human approval channel cannot independently
expand delegated agent authority.

Required verification:
Reproduce authority-expansion denial.

## P05 — Seller Request Authority Boundary

Commit: 1119002
Status: COMMITTED

Claim:
A seller request cannot increase an agent's
authorized payment scope.

Required verification:
Reproduce unauthorized payment denial.

## P06 — Human Admin Credential Boundary

Commit: 14be3e3
Status: COMMITTED

Claim:
Possession of human administrator credentials
does not independently grant agent authority.

Required verification:
Reproduce the relevant denial.

## P07 — Manufacturing Authority Boundary

Commit: a4c4ca5
Status: COMMITTED

Claim:
Manufacturing-plan changes do not silently
expand delegated authority.

Required verification:
Inspect and rerun the adversarial regression.

## P08 — Current Parent Authority

Commit: f1373ae
Status: COMMITTED

Claim:
Derived execution requires currently valid
parent authority.

Required verification:
Reproduce stale-parent and revoked-parent cases.

## P09 — Execution Evidence Substitution

Commit: a4160df
Status: COMMITTED

Claim:
Execution evidence cannot be substituted across
state commitments without detection.

Required verification:
Reproduce evidence-substitution denial.

## P10 — Execution Evidence Authentication

Commit: 5fe9cb3
Status: COMMITTED

Claim:
Execution evidence must be authenticated
before state commitment.

Required verification:
Reproduce invalid-evidence rejection.

## P11 — Forged Execution Evidence

Commit: 9f694ae
Status: COMMITTED

Claim:
Forged execution evidence must not be accepted
as sufficient commitment evidence.

Required verification:
Reproduce forged-evidence denial.

## P12 — Execution-Linked Commitment Evidence

Commit: d59e050
Status: COMMITTED

Claim:
State commitment requires evidence linked
to the actual execution.

Required verification:
Reproduce invalid-linkage denial.

## P13 — Suppressed Evidence Bypass

Commit: b9a900d
Status: COMMITTED

Claim:
Suppressing required execution evidence must
not permit state commitment.

Required verification:
Reproduce missing-evidence denial.

## P14 — Failed Execution Commitment

Commit: e5a4bfe
Status: COMMITTED

Claim:
Failed execution evidence must block
subsequent state commitment.

Required verification:
Reproduce fail-closed commitment behavior.

## P15 — Missing Execution Evidence

Commit: a7a5172
Status: COMMITTED

Claim:
Missing execution evidence must not be treated
as successful authorization to commit state.

Required verification:
Reproduce missing-evidence scenario.

## P16 — Mandatory Current Authority

Commit: 06b42a4
Status: COMMITTED

Claim:
Current-authority enforcement must be mandatory
in the execution path.

Required verification:
Confirm bypass attempts fail closed.

## P17 — Guarded Execution Revalidation

Commit: 1994e8e
Status: COMMITTED

Claim:
Authority must be revalidated at execution time.

Required verification:
Reproduce authority changes between initial
authorization and execution.

## P18 — Industrial Shutdown Boundary

Commit: f585c60
Status: COMMITTED

Claim:
Industrial inspection authority does not
automatically grant shutdown authority.

Required verification:
Reproduce unauthorized shutdown denial.

## P19 — Authority Contraction Documentation

Commit: f734c80
Status: COMMITTED

Claim:
Partial authority contraction is documented
as an adversarial validation class.

Required verification:
Inspect the documented gap and test coverage.

## P20 — Execution-Time Revocation

Commit: 60d7a7a
Status: COMMITTED

Claim:
Authority revoked before execution must
prevent the consequential action.

Required verification:
Reproduce execution-time revocation denial.

## Planned Adversarial Proofs

### A01 — Approval-to-Execution Binding

Status: PLANNED

Test whether material changes between human
approval and execution invalidate approval:

- Action
- Target
- Amount
- Context
- Authority state
- Timing

Expected:
No unauthorized execution or state commitment.

### A02 — Capability Composition

Status: PLANNED

Individually authorized capabilities must not
combine into an unauthorized consequential action.

### A03 — Multi-Agent Delegation

Status: PLANNED

A delegated worker must not exceed the original
human authority through intermediate agents.

### A04 — Long-Horizon Authority

Status: PLANNED

Previously valid authority must not survive
revocation, expiration, or supersession merely
because a workflow remains active.

### A05 — External Operator Validation

Status: PLANNED

An independent operator should reproduce
supported authorization and denial outcomes
using documented interfaces and evidence.

## Verification Procedure

Before upgrading COMMITTED to REPRODUCED:

1. Inspect the relevant commit and changed files.
2. Identify the actual executable regression.
3. Run the regression against the intended HEAD.
4. Record expected and observed results.
5. Confirm denial blocks consequential execution.
6. Confirm evidence and replay behavior.
7. Record any limitations or failures.

Do not infer security guarantees solely from
a successful Git commit or passing assertion.

## Recovery Sources

ARCHITECTURE.md
docs/POST_V1_AUTHORITY_ENFORCEMENT.md
docs/DECISION_REPLAY.md
docs/RESPONSIBILITY_CHAIN.md
docs/recovery/CURRENT_STATE.md
docs/recovery/AUTHORITY_RULES.md

Git history, source code, and test evidence
remain authoritative.

## Verified Proof Update — 2026-11-09

Branch: post-v1-authority-continuation
Commit: d57ccee
Previous checkpoint: 5042098

### Historical V-008 Replay
Status: REPRODUCED

- Test: test_historical_v008_replay.py
- Historical verifier commit: 542b6e7
- Historical evidence: validation/v008_evidence_bundle.json
- Historical cross-process replay: PASS
- Original evidence byte comparison: PASS
- Tampered decision ID rejected: PASS
- Current production verifier unchanged.

### Composed Authority Denial
Status: REPRODUCED

- Test: test_replay_composed_authority_not_delegated.py
- Trusted-key registry supplied to denial replay.
- Undelegated composed authority rejected.
- Independently reproduced denial: PASS

### Targeted Security Regression
Status: PASS

Five scripts completed successfully:
- Historical V-008 replay
- Independent human approval
- Execution-time revocation
- Approval-to-decision binding
- Composed-authority denial replay

### Limitations
- Full repository regression suite not yet confirmed clean.
- Historical hash integrity is not independent signer authentication.
- Historical verification must not authorize live execution.
- Existing planned adversarial scenarios remain planned
  until their specific proofs are verified.

## Verified Regression Evidence - 2026-11-10

Branch: post-v1-authority-continuation
Engineering HEAD: a75d618

### Git Evidence
- 571a8fa: Isolate generated V-008 evidence and repair cross-resource replay.
- a75d618: Authenticate execution evidence in end-to-end replay fixture.

### Verified Proofs
- Historical V-008 replay: PASS.
- Historical evidence tampering rejected: PASS.
- Original V-008 evidence preserved: PASS.
- Cross-resource authority denial replay: PASS.
- Authenticated execution and state commitment: PASS.
- State receipt and state record verification: PASS.
- Stored-state verification: PASS.
- All 73 root-level regression scripts: PASS.
- Post-regression repository integrity: PASS.

### Evidence Preservation
- Historical fixture: validation/v008_evidence_bundle.json
- Generated fixture: validation/v008_generated_evidence_bundle.json
- Generated evidence must not overwrite historical proof.
- Production verifier remains unchanged.
- Existing .before_ safety backups remain untouched.

### Verification Scope
- Root-level test_*.py scripts completed successfully.
- Nested and external integration verification not yet established.
- Independent external operator reproduction remains pending.

## Standalone External Verifier Proof - 2026-11-10

Baseline Git HEAD: 3f312c0

### Positive Verification
Command:
python3 external_replay_verifier.py validation/v008_generated_evidence_bundle.json

Observed:
- passed: True
- status: VERIFIED
- failed_checks: []

### Negative Verification
- Created a temporary copy of the generated evidence.
- Replaced intent_receipt.decision_id with TAMPERED-DECISION.
- Executed the standalone verifier against the modified copy.

Observed:
- passed: False
- status: FAILED_CLOSED
- Nonzero process exit status.
- intent_receipt_signature: FAIL
- intent_linkage: FAIL

### Integrity
- Original historical V-008 evidence unchanged.
- Tracked working tree remained clean after verification.
- No production verification code modified.

### Scope and Limitations
- Standalone evidence-chain validation demonstrated locally.
- Independent Ed25519 trust-root verification not established by this proof.
- Execution-time authority enforcement not independently reproduced.
- External third-party operator reproduction remains pending.
