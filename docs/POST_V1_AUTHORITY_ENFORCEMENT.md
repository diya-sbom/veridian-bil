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

## Derived Capability After Configuration Rollback or Revocation

Adversarial validation class:

`DERIVED_CAPABILITY_SURVIVES_CONFIGURATION_ROLLBACK`

Veridian must not treat possession of a derived capability, token, credential, or previously acquired execution path as continuing authority after the underlying authority condition has been denied, rolled back, or revoked.

Two validation proofs currently establish this boundary:

1. Unauthorized derived-capability path fails closed.
   An attempted internal configuration change outside delegated authority is denied with `OUT_OF_SCOPE`, produces no executable intent, produces no derived token or confidential-data access, and the denial is independently replayable.
   Proof commit: `89c082b`.

2. Already-issued derived capability does not survive authority revocation.
   A credential may remain physically present after issuance, but when the underlying authority state becomes `REVOKED`, a subsequent protected action fails with `REVOKED_AUTHORITY`, execution fails closed, and replay independently reproduces the denial.
   Proof commit: `e5efe4b`.

These proofs validate existing authority-enforcement behavior. They do not introduce a credential lifecycle, token revocation system, secrets manager, or IAM architecture into Veridian.

## Authority Scope to Intended Action

Authority scope is evaluated against the intended action using an explicit,
deterministic mapping. No fuzzy, substring, or semantic matching is permitted.

Current governed mapping:

- `Production Deployment` -> `DEPLOY`

If the authority scope does not explicitly authorize the intended action,
authority validation must fail closed with `OUT_OF_SCOPE`.

Additional scope-to-action mappings require an explicit governance definition
before they may be accepted.

## Dynamic Authority Contraction

Execution-time full revocation is supported and validated.

Proof commit: `60d7a7a`

The validation demonstrates:

- authority may be valid when a task begins;
- authority may become revoked before a later execution attempt;
- execution-time validation uses the current authority state;
- the previously permitted action is denied with `REVOKED_AUTHORITY`;
- no executable intent is produced;
- execution fails closed;
- denial is independently replayable.

### Remaining Gap: Partial Active Contraction

Veridian does not yet establish a canonical mechanism for replacing or superseding an ACTIVE delegated authority with a narrower ACTIVE authority boundary during an ongoing task.

Existing resource-binding and delegation-lineage rules prevent authority expansion and preserve parent resource boundaries, but they do not by themselves establish dynamic replacement of an existing ACTIVE grant.

Therefore partial contraction such as:

`ACTIVE authority over {A,B} -> ACTIVE authority over {A}`

must not yet be claimed as validated behavior.

No architecture change is introduced by this finding.

## Execution-Time Revalidation Gap

A newly reproduced validation case shows that a previously VERIFIED IntentRecord can still execute after its underlying authority has been revoked.

Observed sequence:

- Payment authority is ACTIVE.
- Exact `EXECUTE_PAYMENT` intent is VERIFIED.
- IntentReceipt and IntentRecord are created.
- Authority later becomes `REVOKED`.
- The original, unchanged VERIFIED IntentRecord is presented to the executor.
- The current executor returns `EXECUTED`.

This exposes an authorization-to-execution time-of-check/time-of-use gap.

Principle:

`previously verified authorization != current execution authority`

A valid signed or verified authorization record must not become a bearer capability that survives revocation.

Required future invariant:

- authority must still be current at the execution boundary;
- revoked, expired, exhausted, or contracted authority must block execution;
- no unauthorized resulting state may occur;
- denial evidence must remain independently replayable.

Current reproducer:

`test_stale_verified_payment_after_revocation.py`

The original reproducer intentionally demonstrates the unsafe direct-executor behavior.

A guarded execution boundary is now implemented in:

`executor/guarded_execution.py`

Validation demonstrates both directions:

- current ACTIVE authority is freshly revalidated and executes successfully;
- the same previously VERIFIED action, after authority becomes REVOKED, is denied with `REVOKED_AUTHORITY`;
- the resulting execution fails closed with no executable action.

Regression proof:

`test_guarded_execution_revocation.py`

Execution surface migration:

The former public `execute_intent()` entry point has been removed from active Python code.

The low-level execution primitive is now explicitly internal:

`_execute_verified_intent()`

Production execution routes through:

`execute_with_current_authority()`

which performs fresh authority validation immediately before execution.

Regression validation confirms that:

- current ACTIVE authority still permits legitimate execution;
- REVOKED authority fails closed;
- cumulative exhaustion remains enforced;
- resource binding remains enforced;
- adaptive retries do not expand authority;
- derived capability does not survive revocation;
- payment mandate limits remain enforced;
- industrial inspection does not create shutdown authority;
- operator instruction does not create target-owner authority;
- replay integrity and tamper detection remain intact.

The internal execution primitive remains available for low-level implementation and test use. Its Python naming convention is not itself a security boundary; consequential application execution must enter through the guarded current-authority path.

## Missing-evidence commitment gap

Adversarial validation identified a downstream integrity gap after execution denial.

Reproducer:

`test_missing_evidence_commit_gap.py`

Observed sequence:

- execution status is `FAILED_CLOSED`;
- `create_state_receipt()` still produces a state receipt with `verification_status="VERIFIED"`;
- `create_state_record()` preserves that apparent VERIFIED state;
- `commit_state()` returns a receipt with `committed=True`.

This demonstrates that successful pre-execution authority enforcement alone is insufficient if downstream evidence and commitment layers can manufacture an apparent valid state transition after execution was denied.

Required invariant:

- a FAILED_CLOSED execution must never produce VERIFIED state evidence;
- missing, suppressed, delayed, or incomplete mandatory evidence must block commitment;
- commitment must depend on valid execution-linked evidence rather than caller-supplied state alone;
- denial or missing-evidence outcomes must remain independently verifiable.

This is a confirmed enforcement/evidence-integrity gap and requires remediation.
