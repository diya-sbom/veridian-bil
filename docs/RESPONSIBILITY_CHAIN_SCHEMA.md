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
| valid_until | RFC3339 | No |
| authority_scope | String | Yes |
| policy_reference | String | Yes |
| evidence_reference | UUID | Yes |

## Field Semantics

- `policy_version`: the exact policy version evaluated for the governed decision and used for continuity checks.

- `policy_reference`: an immutable reference to the governing policy artifact or policy record from which the applicable authority/delegation rules are derived. It does not replace `policy_version`.

- `evidence_reference`: an immutable reference to evidence establishing the authority or delegation represented by the Responsibility Chain. It is distinct from `DecisionObject.evidence_references`, which support the governance decision itself.

- `delegation_time`: records when the delegation was created or accepted. It is provenance data and does not, by itself, establish whether authority is still valid.

- `valid_until`: optional explicit end of authority validity. When present, execution after this time produces `EXPIRED_AUTHORITY`. When absent, expiry must not be inferred.

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

## Deterministic Failure Semantics

- `UNKNOWN_AUTHORITY`: the responsibility chain does not identify a concrete originating decision authority. Missing or blank authority fails closed.

- `BROKEN_CHAIN`: the recorded responsibility path cannot be continuously traced from the governed decision/action back to the originating authority because a required linkage is missing or inconsistent.

- `UNAUTHORIZED_DELEGATION`: a delegator and delegatee are identified, but the available policy and evidence do not establish that the delegator was permitted to grant that authority to that delegatee.

- `EXPIRED_AUTHORITY`: an authority grant was valid previously but was no longer valid at execution time according to explicit authority-validity data. This condition must not be inferred from `delegation_time`.

- `OUT_OF_SCOPE`: the intended action is not explicitly permitted by the recorded `authority_scope`. Unknown scopes and unknown actions fail closed.

These conditions are distinct. Presence of identity is not proof of delegation authority, possession of capability is not proof of authority, and historical authority is not proof of current authority.

## Properties

- Continuous
- Traceable
- Replayable
- Independently Verifiable
- Immutable

## Purpose

The Responsibility Chain preserves accountability from the originating authority through every delegation, autonomous action, and resulting outcome.
