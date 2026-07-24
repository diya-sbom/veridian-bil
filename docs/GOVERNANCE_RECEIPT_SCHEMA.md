# Governance Receipt Schema

## Required Fields

| Field | Type | Required |
|-------|------|----------|
| receipt_id | UUID | Yes |
| decision_id | UUID | Yes |
| timestamp | RFC3339 | Yes |
| authority | String | Yes |
| policy_version | String | Yes |
| evidence_hash | String | Yes |
| execution_status | Enum | Yes |
| state_verification | Enum | Yes |
| integrity_hash | String | Yes |
| verifier | String | Yes |

## Execution Status

APPROVED

DENIED

EXECUTED

FAILED

## State Verification

PASSED

FAILED

UNKNOWN

## Properties

- Immutable
- Tamper-evident
- Independently Verifiable
- Replayable
- Cryptographically Hashable

## Purpose

A Governance Receipt serves as durable evidence that a governance decision, its execution, and its verification can be independently confirmed without relying on the 
originating system.
