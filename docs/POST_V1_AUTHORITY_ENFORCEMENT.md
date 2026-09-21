# Post-v1.0 Authority Enforcement & Adversarial Governance Validation

## Objective

Enforce and independently verify that technical capability does not imply authority.

Before execution, Veridian must determine whether the acting agent is authorized for the intended action under the applicable responsibility chain, delegation scope, and policy.

## Existing Foundation

Veridian already records:

- decision authority;
- responsible party;
- intended action;
- intended state;
- delegation relationships;
- authority scope;
- policy references;
- evidence references.

The Responsibility Chain specification already defines authority and delegation failure conditions.

This phase integrates and enforces those existing governance requirements at the pre-execution boundary.

## Required Failure Conditions

Veridian must deny execution when authority validation produces:

- UNKNOWN_AUTHORITY
- BROKEN_CHAIN
- UNAUTHORIZED_DELEGATION
- EXPIRED_AUTHORITY
- OUT_OF_SCOPE
- AUTHORITY_LIMIT_EXCEEDED

## Cumulative Authority Exhaustion

`AUTHORITY_LIMIT_EXCEEDED`: the intended action is individually permitted by the
recorded authority scope, but executing it would exceed an explicit delegated
limit or consume more authority than remains available at execution time.

Examples include:
- spending ceiling;
- invocation count;
- resource consumption;
- recursion limit;
- bounded time-window usage.

This condition is distinct from `OUT_OF_SCOPE`: the action type may be authorized,
while the remaining delegated allowance is insufficient.

Execution must be denied before the limit is exceeded, and the denial must be
preserved as replayable evidence.

## Primary Adversarial Scenario

An agent legitimately possesses a credential or technical capability that could perform an action, but the action is outside its delegated authority.

Expected behavior:

1. The action is denied before execution.
2. No unauthorized state change is committed.
3. Evidence records why authority validation failed.
4. The denial can be independently replayed and verified.

## Post-Execution Integrity Scenario

For an authorized action that executes successfully:

1. authority is verified before execution;
2. execution occurs within the approved scope;
3. resulting state and evidence remain linked to the authority decision;
4. subsequent state or evidence tampering causes independent verification to fail closed.

## Out of Scope

This phase does not turn Veridian into:

- a secrets manager or vault;
- an IAM platform;
- an endpoint-security product;
- a credential-rotation system;
- a general-purpose policy administration product.

External security systems may provide identity, credentials, secrets, and policy inputs. Veridian governs whether a consequential action is admissible under the supplied and verifiable authority evidence.

## Acceptance Criteria

This phase is complete only when:

- authority is evaluated before execution;
- authority scope is evaluated against the intended action;
- remaining delegated authority is evaluated before execution when explicit cumulative limits apply;
- invalid, out-of-scope, expired, or limit-exceeding authority prevents execution;
- denial evidence is preserved;
- authorized execution remains supported;
- authority decisions can be independently replayed;
- tampering with authority, state, or resulting evidence fails closed.

## Principle

Possession of capability is not proof of authority.

## Authority Scope to Intended Action

Authority scope is evaluated against the intended action using an explicit,
deterministic mapping. No fuzzy, substring, or semantic matching is permitted.

Current governed mapping:

- `Production Deployment` -> `DEPLOY`

If the authority scope does not explicitly authorize the intended action,
authority validation must fail closed with `OUT_OF_SCOPE`.

Additional scope-to-action mappings require an explicit governance definition
before they may be accepted.
