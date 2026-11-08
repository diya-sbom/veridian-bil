# Veridian — Authority Rules

## Purpose

Veridian determines whether a consequential action
is supported by legitimate, current, scoped authority.

Technical capability, possession of credentials,
and successful access do not establish authority.

## Core Principle

Capability to reach a system does not create
authority to act on it.

History is not authority.
Repetition is not permission.
Approval is not authority expansion.

## Rule 1 — Authority Before Execution

Every consequential action must pass authority
verification before execution.

Missing, invalid, or insufficient authority
must fail closed.

## Rule 2 — Scope Binding

Authority must be bound to the intended action,
target, resource, and applicable constraints.

An authorized capability cannot be reused to
perform an unauthorized consequential action.

## Rule 3 — Current Authority

Authority must remain valid at execution time.

Past authorization does not guarantee present
authorization.

Revocation, expiration, contraction, or
supersession must be evaluated against the
current authoritative state.

## Rule 4 — Delegation Lineage

Delegated authority must remain traceable
to its legitimate originating authority.

An agent cannot create authority by instructing
another agent.

Subdelegation must remain within the permitted
scope and limits of the authority chain.

## Rule 5 — Parent Authority

A delegated capability cannot survive revocation
of the authority that permits its execution.

Previously installed or reachable execution
paths do not become permanent authority.

Relevant proof:
877afc6 — Persistent delegation does not
survive parent revocation.

## Rule 6 — Independent Human Approval

Human approval does not independently grant
an AI agent authority.

Approval must come from a genuine, independently
verified human approval source.

Approval must remain valid in the live
execution path.

Relevant proofs:
46eb017 — Approval channel does not create
agent authority.

fdf4446 — Independent human presence for
trusted approval provenance.

0564864 — Independent human approval
enforced at execution.

## Rule 7 — Approval Binding

Human approval must apply to the exact
authorized execution.

Changes to action, target, amount, context,
authority state, or timing must trigger
appropriate revalidation.

A stale approval artifact must not be
treated as continuing permission.

Status:
Next adversarial validation objective.
Not marked fully proven.

## Rule 8 — Economic Authority

Agent spending or business commitments
must remain within explicitly delegated
economic authority.

Seller requests, payment instructions,
or external messages cannot expand
the agent's authority.

Relevant proof:
1119002 — Seller request cannot expand
payment authority.

## Rule 9 — Cumulative Authority

Authority limits must account for
cumulative consequential activity when
the delegation specifies aggregate limits.

Repeated individually permitted operations
must not bypass an aggregate authority cap.

## Rule 10 — Capability Composition

Combining individually permitted capabilities
must not create an unauthorized consequential
execution path.

Effective authority must be checked against
the resulting action, not merely the
individual component permissions.

Status:
Adversarial proof remains to be verified.

## Rule 11 — Evidence Integrity

Authority decisions must preserve evidence
sufficient for independent verification.

Tampering with authority, state, execution
evidence, or record linkage must fail closed.

## Rule 12 — Replay Verification

An independent verifier must be able
to reproduce supported authorization
and denial decisions using the applicable
evidence and governing rules.

Historical evidence cannot replace
current execution-time authorization.

## Rule 13 — No Silent Authority Expansion

Agent instructions, planning, optimization,
adaptive retries, or peer-agent messages
must not silently expand delegated authority.

Permission to perform one action is not
permission to perform another.

## Verification Status

The principles above describe the intended
authority model and existing documented proofs.

A commit reference alone is not sufficient
to establish a verified security guarantee.

For each claimed implementation, inspect:
- Relevant source code.
- Git commit and diff.
- Regression tests.
- PASS and FAIL evidence.
- Independent replay results.

Do not mark a rule fully implemented unless
its actual enforcement and tests are verified.

## Primary Sources

ARCHITECTURE.md
docs/POST_V1_AUTHORITY_ENFORCEMENT.md
docs/RESPONSIBILITY_CHAIN.md
docs/DECISION_REPLAY.md
Git history and executable regression tests.

## Recovery Rule

When starting a new development session,
verify the live repository HEAD and read
CURRENT_STATE.md before making changes.

The repository is the source of truth.
Chat memory is supporting context only.
