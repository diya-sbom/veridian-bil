# Admissibility Schema

## Required Fields

| Field | Type | Required |
|-------|------|----------|
| admissibility_id | UUID | Yes |
| decision_id | UUID | Yes |
| authority_verified | Boolean | Yes |
| responsibility_chain_verified | Boolean | Yes |
| policy_verified | Boolean | Yes |
| evidence_verified | Boolean | Yes |
| replay_verified | Boolean | Yes |
| execution_verified | Boolean | Yes |
| state_verified | Boolean | Yes |
| receipt_verified | Boolean | Yes |
| admissibility_result | Enum | Yes |
| reviewer | String | Yes |
| review_timestamp | RFC3339 | Yes |

## Admissibility Results

ADMISSIBLE

NOT_ADMISSIBLE

REQUIRES_REVIEW

## Validation Rules

- Authority must be verified.
- Responsibility chain must be complete.
- Policy version must be identified.
- Evidence must be independently verifiable.
- Decision Replay must succeed.
- Execution must match the approved decision.
- Resulting state must be verified.
- Governance Receipt must be valid.

## Failure Conditions

- Unknown Authority
- Broken Responsibility Chain
- Missing Evidence
- Replay Failure
- Policy Mismatch
- Unauthorized Execution
- State Verification Failure
- Invalid Governance Receipt

## Properties

- Independent
- Deterministic
- Auditable
- Replayable
- Evidence-Based

## Purpose

The Admissibility Schema defines the objective criteria for determining whether an autonomous governance decision has sufficient independently verifiable evidence to be 
accepted as trustworthy.
