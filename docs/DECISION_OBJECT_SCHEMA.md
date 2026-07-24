# Decision Object Schema

## Required Fields

| Field | Type | Required |
|-------|------|----------|
| decision_id | UUID | Yes |
| timestamp | RFC3339 | Yes |
| authority | String | Yes |
| responsible_party | String | Yes |
| policy_version | String | Yes |
| evidence | Array | Yes |
| decision | Enum | Yes |
| intended_action | String | Yes |
| intended_state | Object | Yes |
| actual_action | String | Yes |
| actual_state | Object | Yes |
| verification | Enum | Yes |
| governance_receipt | UUID | Yes |

## Decision Values

APPROVED

DENIED

REQUIRES_REVIEW

## Verification Values

PASSED

FAILED

UNKNOWN

## Properties

- Immutable
- Replayable
- Traceable
- Independently Verifiable
