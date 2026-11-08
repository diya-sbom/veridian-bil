# Veridian — Chat and Engineering Recovery

## Purpose

Recover Veridian after a lost ChatGPT conversation,
new AI assistant, developer handoff, or long absence.

The repository is the source of truth.

Never reconstruct implementation facts from
AI memory alone.

## Repository Location

~/Desktop/APEX/decisionassure/veridian-bil

Historical branch:
post-v1-authority-continuation

Historical engineering checkpoint:
877afc6

Commit subject:
Prove persistent delegation does not
survive parent revocation.

These values are historical.
Always verify the current Git state.

## Start Recovery

Open a terminal and run:

cd ~/Desktop/APEX/decisionassure/veridian-bil

git branch --show-current
git log -5 --oneline
git status --short

Do not reset, clean, checkout, merge,
rebase, or overwrite files during recovery.

Preserve existing .before_ safety backups.

## Read Recovery Documents

Read these files in order:

1. docs/recovery/CURRENT_STATE.md
2. docs/recovery/AUTHORITY_RULES.md
3. docs/recovery/PROOF_INDEX.md
4. docs/recovery/ARCHITECTURE.md
5. docs/recovery/NEXT_STEPS.md
6. docs/recovery/ACQUISITION_READINESS.md

Also inspect the root ARCHITECTURE.md
and relevant original specifications.

## Evidence Hierarchy

Prefer:

1. Live Git state and source code.
2. Executable tests and observed results.
3. Verification records and replay evidence.
4. Committed architecture and specifications.
5. Recovery documents.
6. Previous conversation context.

Never treat a commit title as sufficient
proof of a security guarantee.

## Engineering Continuation

At the historical checkpoint, the next
engineering objective was:

Approval-to-execution binding.

Prove that previously valid human approval
cannot authorize a materially changed action.

Test changes to:

- Action
- Target
- Amount
- Context
- Authority state
- Timing

Also test stale or substituted approval
artifacts.

The expected result is fail-closed denial
without unauthorized execution or state commit.

An unchanged, currently authorized action
with valid approval should still succeed.

Before starting, check whether newer
commits already completed this work.

## Core Architecture

Decision
  |
Governance Receipt
  |
Diya Verification
  |
Intent Record
  |
Executor
  |
MIRA Verification
  |
State Record
  |
AFS Commit
  |
BIL Commit Record
  |
State Store
  |
Replay Verification

Refer to root ARCHITECTURE.md for details.

Do not redesign or restart the architecture.

## Governing Principles

Capability to reach a system does not
create authority to act on it.

History is not authority.

Repetition is not permission.

Human approval does not create or
expand agent authority.

Authority must remain current and scoped
at the moment of consequential execution.

Revoked parent authority cannot sustain
dependent delegation.

Invalid authorization must fail closed.

Evidence must support independent replay.

## Verification Requirements

Before committing engineering changes:

- Identify the existing enforcement path.
- Establish a valid PASS case.
- Establish unauthorized FAIL cases.
- Confirm denial happens before execution.
- Confirm unauthorized state does not commit.
- Confirm denial evidence is preserved.
- Confirm independent replay succeeds.
- Run relevant regression tests.
- Review staged changes.

Do not claim external validation solely
from successful local tests.

## Recovery Pack Maintenance

After every major engineering checkpoint:

- Update CURRENT_STATE.md.
- Update PROOF_INDEX.md.
- Update NEXT_STEPS.md.
- Record regression commands and results.
- Record newly discovered limitations.
- Commit recovery changes deliberately.

Keep historical proof records intact.

Do not silently change the meaning
of existing evidence or record fields.

## Acquisition Readiness

Target: May 2027.

This is a target, not a guarantee.

Priority requirements include:

- Reproducible security enforcement.
- Independent external verification.
- Non-bypassable integration.
- Documented architecture.
- Transferable operation.
- Clear intellectual property ownership.
- Credible commercial validation.
- Reviewable acquisition materials.

See ACQUISITION_READINESS.md.

## New Chat Recovery Prompt

Copy the following into a new AI conversation:

Continue the Veridian project from its
existing repository and latest Git HEAD.

The repository is located at:

~/Desktop/APEX/decisionassure/veridian-bil

Recovery documentation is in:

docs/recovery/

First verify the live branch, HEAD,
and working-tree status.

Read CURRENT_STATE.md, AUTHORITY_RULES.md,
PROOF_INDEX.md, ARCHITECTURE.md,
NEXT_STEPS.md, ACQUISITION_READINESS.md,
and CHAT_RECOVERY.md.

The historical checkpoint was 877afc6,
which proved persistent delegation does
not survive parent revocation.

Do not assume this remains the latest HEAD.

Continue the highest-priority unfinished
adversarial validation.

Preserve the existing architecture,
all completed proofs, and .before_ backups.

Do not restart the project.

Give one safe terminal step at a time.
Inspect evidence before making changes.

Do not confuse technical access,
capability, human approval, or historical
permissions with current delegated authority.

## Final Recovery Rule

A new engineer or AI assistant must be able
to determine:

- What the system is designed to do.
- What has actually been implemented.
- Which proofs have been reproduced.
- Which guarantees remain unverified.
- What should be done next.
- How to reproduce the relevant evidence.

The project must remain recoverable
without any particular chat conversation.

Veridian's continuity belongs in the
repository, not in AI memory.
