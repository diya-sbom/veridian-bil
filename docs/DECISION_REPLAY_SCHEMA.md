# Decision Replay Schema

## Required Fields

| Field | Type | Required |
|-------|------|----------|
| replay_id | UUID | Yes |
| decision_id | UUID | Yes |
| replay_timestamp | RFC3339 | Yes |
| replay_authority | String | Yes |
| evidence_set | Array | Yes |
| policy_version | String | Yes |
| reconstructed_decision | Enum | Yes |
| reconstructed_state | Object | Yes |
| replay_result | Enum | Yes |
| verifier | String | Yes |

## Replay Results

MATCH

MISMATCH

INCOMPLETE

FAILED

## Validation Rules

- Every replay must use preserved evidence.
- Replay must not depend on the original decision-maker.
- The reconstructed decision must match the recorded decision.
- Policy references must resolve to the correct version.

## Failure Conditions

- Missing Evidence
- Policy Version Mismatch
- Decision Mismatch
- State Mismatch
- Corrupted Receipt
- Verification Failure

## Properties

- Deterministic
- Independently Verifiable
- Replayable
- Immutable
- Auditable

## Purpose

Decision Replay demonstrates that an independent reviewer can reconstruct the original governance decision using only preserved evidence, policies, and recorded outcomes.
