# Veridian — Architecture Recovery Guide

## Purpose

This document helps a new engineer or AI assistant
recover Veridian's architecture and continue work
without relying on previous ChatGPT conversations.

This is a navigation and recovery document.

The existing architecture, source code, Git
history, and executable tests remain authoritative.

## Repository

Path: ~/Desktop/APEX/decisionassure/veridian-bil

Branch at recovery checkpoint:
post-v1-authority-continuation

Verified checkpoint:
877afc6

Always verify the live HEAD before continuing.

## Primary Architecture Source

Read the repository root:

ARCHITECTURE.md

Also inspect:

README.md
DESIGN_DECISIONS.md
docs/POST_V1_AUTHORITY_ENFORCEMENT.md
docs/RESPONSIBILITY_CHAIN.md
docs/DECISION_REPLAY.md

Do not replace these documents with this guide.

## Documented Runtime Flow

Decision
  |
  v
Governance Receipt
  |
  v
Diya Verification
  |
  v
Intent Record
  |
  v
Executor
  |
  v
MIRA Verification
  |
  v
State Record
  |
  v
AFS Commit
  |
  v
BIL Commit Record
  |
  v
State Store
  |
  v
Replay Verification

Source: Root ARCHITECTURE.md

## Governance and Authority

Veridian evaluates whether a consequential action
is supported by legitimate, current, scoped authority.

Authority must be established independently
of technical capability or system access.

Governance and authority checks must occur
before the consequential action executes.

A human approval artifact alone cannot create
or expand delegated agent authority.

## Diya — Pre-Execution Verification

Diya is the pre-execution verification layer.

Its role in the documented architecture is
to verify the admissibility of a proposed action
before the executor performs it.

The intended security boundary is:

Invalid authority or verification must
prevent the protected action from executing.

Actual implementation and bypass resistance
must be verified through code and tests.

## Executor — Consequential Action

The executor performs the permitted action
only after the required verification gates pass.

Its execution path must not silently bypass
current authority or trusted approval checks.

Relevant implementation areas include:

executor/
decisionassure/

Inspect source code before changing behavior.

## MIRA — State Integrity

MIRA verifies resulting state and evidence
before state commitment.

The intended boundary is:

Invalid or insufficient state evidence
must prevent unauthorized commitment.

Relevant implementation area:

mira/

Inspect the implementation and regression
tests to confirm the enforced boundary.

## AFS — Atomic Commitment

AFS governs the commitment of verified state.

The intended requirement is that protected
state changes are committed consistently
and cannot bypass required verification.

The recovery process must confirm this
through actual commit-path tests.

## BIL — Evidence and Continuity

BIL records commitment evidence and supports
history and replay verification.

The architecture describes commit records,
state linkage, and verification of evidence.

Do not assume every history-continuity or
cryptographic guarantee is complete merely
because a component is documented.

Inspect the current implementation and tests.

## Replay Verification

Replay verification should independently
reproduce supported authorization and
denial outcomes from relevant evidence.

Important properties include:

- Evidence integrity
- Correct authority linkage
- Deterministic decisions
- Tampering detection
- Fail-closed outcomes

Local regression success is distinct from
independent external validation.

## Authority Enforcement Boundaries

The recovery process must preserve:

1. Authority before execution.
2. Action and resource scope binding.
3. Current authority at execution time.
4. Bounded delegation lineage.
5. Parent revocation enforcement.
6. Independent human approval provenance.
7. Cumulative authority constraints.
8. Execution evidence integrity.
9. Verification before state commitment.
10. Independent replay of decisions.

See:

docs/recovery/AUTHORITY_RULES.md

## Latest Verified Engineering Work

Commit:
877afc6

Subject:
Prove persistent delegation does not
survive parent revocation.

Related implementation:
decisionassure/decision_replay.py

Related regression:
test_compromised_application_identity_persistent_derived_authority.py

The regression was reproduced locally
on November 7, 2026.

See:

docs/recovery/PROOF_INDEX.md

## Architecture Verification Procedure

Before modifying any architectural component:

1. Verify Git branch and HEAD.
2. Inspect the working tree.
3. Read the relevant existing specification.
4. Trace the actual source-code execution path.
5. Identify the authority-enforcement boundary.
6. Identify PASS and FAIL regression tests.
7. Check that denial prevents execution.
8. Check that invalid state cannot commit.
9. Check evidence and replay behavior.
10. Record remaining limitations.

Do not infer enforcement solely from
architecture diagrams or documentation.

## Change Control

Preserve the existing system architecture.

Avoid unrelated refactoring.

Changes affecting authority, verification,
execution, or commitment require review
proportional to their security impact.

Run relevant regression tests before committing.

Do not delete existing .before_ safety backups.

## Recovery Priority

When a new engineer or assistant joins:

First establish what is implemented.

Then establish what is independently verified.

Then identify the next unproven security boundary.

Do not restart the architecture based on
an incomplete understanding of the repository.

## Recovery Principle

Capability to reach a system does not create
authority to act on it.

The same discipline applies to development:

Access to code does not establish that a
security guarantee has been proven.

Repository evidence must support each claim.
