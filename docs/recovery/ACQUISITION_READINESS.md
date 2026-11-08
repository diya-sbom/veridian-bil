# Veridian — Acquisition Readiness

## Purpose

Define the technical, operational, legal,
and commercial requirements for making
Veridian credible to potential acquirers.

Target readiness date: May 2027.

This is a readiness framework, not a claim
that Veridian is currently acquisition-ready.

## Current Engineering Checkpoint

Branch: post-v1-authority-continuation

Latest verified engineering HEAD:
877afc6 — Prove persistent delegation does
not survive parent revocation.

Verify the live HEAD before relying on this
historical checkpoint.

## Acquisition Thesis

Veridian is designed to enforce legitimate,
current, scoped authority for consequential
AI-agent actions and resulting state changes.

Its potential value depends on whether
organizations need independent controls
that agents cannot bypass or expand.

The central principle is:

Capability to reach a system does not
create authority to act on it.

Market demand, defensibility, valuation,
and acquisition interest remain unproven
until independently supported.

## Gate 1 — Technical Enforcement

Requirements:

- Authority verified before execution.
- Intended action bound to authorized scope.
- Revocation enforced at execution time.
- Delegation lineage independently checked.
- Human approval independently verified.
- Cumulative authority limits enforced.
- Unauthorized execution fails closed.
- Invalid state commitment is prevented.
- Evidence tampering is detected.
- Relevant decisions can be replayed.

Acceptance:

Representative PASS and FAIL cases must be
reproducible through documented commands.

Status:
PARTIALLY DEMONSTRATED.

Additional proof coverage remains necessary.

## Gate 2 — Adversarial Validation

Required proof classes:

1. Approval-to-execution binding.
2. Capability composition.
3. Multi-agent delegation expansion.
4. Long-horizon authority changes.
5. Persistent capability after revocation.
6. Evidence substitution or suppression.
7. Execution-path bypass attempts.
8. State-commitment bypass attempts.

Existing evidence must be verified before
claiming a proof class is complete.

Status:
IN PROGRESS.

See PROOF_INDEX.md and NEXT_STEPS.md.

## Gate 3 — Independent Verification

Requirements:

- Independent operator runs the system.
- Operator reproduces PASS and FAIL cases.
- Verification does not depend on ChatGPT.
- Evidence is inspectable.
- Replay results are reproducible.
- Known limitations are documented.
- Failures are recorded and corrected.

Acceptance:

At least one independent technical operator
successfully reproduces the documented
security boundaries.

Status:
NOT YET CONFIRMED.

## Gate 4 — Integration and Dependency

Requirements:

- Documented integration interface.
- Clear installation and setup procedure.
- Representative external system integration.
- Protected execution cannot bypass the gate.
- Removing enforcement breaks the protected
  workflow rather than silently allowing it.
- Authorized actions continue functioning.

Acceptance:

An external integration demonstrates that
Veridian is a required control for selected
consequential actions.

Status:
REQUIRES EXTERNAL VALIDATION.

## Gate 5 — Architecture and Documentation

Requirements:

- Current architecture documentation.
- Defined trust boundaries.
- Versioned schemas where applicable.
- Documented verification interfaces.
- Documented failure behavior.
- Reproducible regression commands.
- Evidence and proof index.
- Clear deployment instructions.
- Recovery documentation.
- Known limitations.

Acceptance:

A new engineer can understand and reproduce
the supported implementation without
depending on the original developer.

Status:
RECOVERY PACK IN PROGRESS.

## Gate 6 — Security and Trust

Requirements:

- Defined trust-root assumptions.
- Documented key lifecycle and rotation.
- Authenticated evidence where required.
- Protection against replay and substitution.
- Revocation and expiration handling.
- Execution-time revalidation.
- No silent authority expansion.
- Threat model covering realistic attackers.
- Independent security review.

Acceptance:

Security assumptions and residual risks
are explicit and reviewable.

Status:
FURTHER VALIDATION REQUIRED.

Do not claim formal certification or
independent audit without supporting evidence.

## Gate 7 — Intellectual Property

Requirements:

- Clear ownership of source code.
- Review of contributor rights.
- Review of third-party dependencies.
- Clear license obligations.
- Identification of proprietary components.
- Documentation of inventions and trade secrets.
- Secure handling of confidential materials.
- Review of trademark and company ownership.
- Counsel review before material transactions.

Acceptance:

A prospective buyer can conduct IP diligence
without unresolved ownership surprises.

Status:
NOT YET VERIFIED.

Legal conclusions require qualified counsel.

## Gate 8 — Commercial Evidence

Requirements:

- Defined target customers.
- Specific costly problem demonstrated.
- Evidence of customer willingness to adopt.
- Quantified operational value where possible.
- Competitive alternatives documented.
- At least one credible external validation.
- Clear deployment and support model.
- Commercial licensing strategy.
- Defensible differentiation.

Acceptance:

Commercial claims are supported by actual
customer evidence, not projected valuations.

Status:
NOT YET VERIFIED.

## Gate 9 — Operational Transferability

Requirements:

- Source repository accessible to authorized
  future maintainers.
- Reproducible development environment.
- Documented dependency versions.
- Test and release procedures.
- Safe backup and recovery process.
- Clear ownership of critical components.
- No dependence on a single AI conversation.
- New engineer onboarding procedure.
- Independent ability to diagnose failures.

Acceptance:

A qualified engineer can operate, test,
and maintain Veridian without its founder.

Status:
IN PROGRESS.

## Gate 10 — Transaction Preparation

Requirements:

- Accurate technical summary.
- Architecture and security evidence.
- IP and license inventory.
- Dependency inventory.
- Demonstration environment.
- Independent validation report.
- Commercial evidence and customer pipeline.
- Known risks and unresolved gaps.
- Financial and legal diligence materials.
- Confidential disclosure strategy.

Acceptance:

Materials are organized for credible
technical and business due diligence.

Status:
NOT STARTED OR NOT YET VERIFIED.

## Readiness Decision

Veridian should not be labeled
ACQUISITION-READY solely because:

- Its architecture is complete on paper.
- Regression tests pass locally.
- The Git history contains many proofs.
- Its creator believes the market is large.
- A target completion date has arrived.

The readiness decision requires objective
evidence across technical, security,
operational, legal, and commercial gates.

## May 2027 Target

The target is to establish a credible,
independently reviewable acquisition position
by May 2027.

Priority sequence:

1. Complete the Recovery Pack.
2. Finish the highest-impact authority proofs.
3. Reproduce the full enforcement chain.
4. Obtain independent external validation.
5. Demonstrate real integration dependency.
6. Complete IP and security documentation.
7. Validate commercial interest.
8. Prepare acquisition diligence materials.

This sequence may change based on evidence.

## Current Immediate Action

Finish the seven-file Recovery Pack.

Verify and commit documentation separately
from source-code changes.

Then resume approval-to-execution binding
as the next adversarial engineering priority.

## Sources

ARCHITECTURE.md
docs/POST_V1_AUTHORITY_ENFORCEMENT.md
docs/recovery/CURRENT_STATE.md
docs/recovery/AUTHORITY_RULES.md
docs/recovery/PROOF_INDEX.md
docs/recovery/NEXT_STEPS.md

Git history, executable regressions,
and independent evidence remain authoritative.

## Final Principle

An acquisition-ready security system must
survive independent technical scrutiny.

Its value cannot depend on one developer,
one assistant, or one conversation.

Veridian must be understandable,
reproducible, transferable, and useful.
