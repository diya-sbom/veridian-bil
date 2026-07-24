# Responsibility Chain Schema

## Required Fields

| Field | Type | Required |
|-------|------|----------|
| chain_id | UUID | Yes |
| organization | String | Yes |
| business_owner | String | Yes |
| decision_authority | String | Yes |
| ai_system | String | Yes |
| agent | String | Yes |
| sub_agent | String | No |
| delegated_by | String | Yes |
| delegated_to | String | Yes |
| delegation_time | RFC3339 | Yes |
| authority_scope | String | Yes |
| policy_reference | String | Yes |
| evidence_reference | UUID | Yes |

## Validation Rules

- Every delegation must identify both delegator and delegate.
- Authority must never be anonymous.
- Responsibility cannot terminate before the resulting outcome.
- Delegation must remain within the approved authority scope.

## Failure Conditions

- Unknown Authority
- Broken Chain
- Unauthorized Delegation
- Expired Authority
- Out-of-Scope Delegation

## Properties

- Continuous
- Traceable
- Replayable
- Independently Verifiable
- Immutable

## Purpose

The Responsibility Chain preserves accountability from the originating authority through every delegation, autonomous action, and resulting outcome.
