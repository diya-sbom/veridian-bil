# Veridian Secure Development Policy v1.0

Status: DRAFT — Pending formal approval
Owner: Veridian Project Owner
Classification: Internal — Confidential
Version: 1.0
Review: Before commercial release and at least annually

## 1. Purpose

Protect Veridian's intellectual property, source code,
confidential information, development environment,
dependencies, security evidence, and release integrity.

This policy governs development practices. It does not
change Veridian's product architecture.

## 2. AI-Generated Code

- Treat AI-generated code as untrusted until reviewed.
- Require human authorization for security-sensitive changes.
- Inspect changes for hidden behavior, insecure defaults,
  unauthorized network activity, and scope expansion.
- Preserve existing security invariants and regressions.
- Never treat AI-generated approval as human approval.

## 3. Confidential Information

- Never commit private keys, credentials, tokens, or secrets.
- Do not disclose proprietary or customer information to
  unapproved external services.
- Use approved secret-management mechanisms.
- Restrict access to confidential engineering assets.
- Revoke or rotate exposed credentials promptly.
- Document suspected information-security incidents.

## 4. Dependency Security

- Use approved and traceable dependency sources.
- Review new dependencies for security and license risks.
- Pin dependencies and verify integrity where practical.
- Investigate material vulnerabilities before release.
- Maintain an SBOM or equivalent dependency inventory.
- Protect build tools and dependency installation workflows.

## 5. Mandatory Review

Review depth follows authority impact and blast radius,
not the number of changed lines.

Red-zone changes include:
- Authority enforcement, delegation, and revocation.
- Trust roots, signatures, and key management.
- Payments and consequential execution.
- Protected state and transaction atomicity.
- Evidence integrity and independent verification.
- Security gates, deployment, and release controls.

Red-zone changes require documented human review,
relevant regression evidence, and explicit authorization
before merge or release.

Independent review must not be claimed unless performed.

## 6. Repository Protection

- Protect release branches with required security checks.
- Restrict force pushes and unauthorized bypasses.
- Require appropriate reviews for protected changes.
- Enforce least-privilege repository access and MFA.
- Protect development machines, backups, and signing keys.
- Preserve existing recovery materials and security evidence.
- Do not commit unreviewed temporary or sensitive files.

## 7. Testing and Evidence

- Preserve existing positive and adversarial regressions.
- Demonstrate that denied actions cause no unauthorized
  durable state change.
- Distinguish authorization from actual execution outcomes.
- Preserve reproducible evidence for security claims.
- Clearly distinguish internal tests from external validation.

## 8. Release Integrity

Before external commercial release:
- Identify the exact approved source commit.
- Verify required tests and security reviews.
- Review dependencies and applicable licenses.
- Record artifact hashes and available provenance.
- Protect release-signing credentials.
- Verify release contents and rollback procedures.
- Block release for unresolved critical security failures.
- Obtain explicit authorization from the release owner.

## 9. Incidents and Exceptions

Record and investigate security incidents.

Exceptions require explicit approval, documented scope,
justification, compensating controls, and an expiration date.

Exceptions must not silently weaken mandatory enforcement
of consequential actions.

## 10. Commercial Claims

- Make only evidence-supported technical claims.
- Do not claim regulatory certification without certification.
- Do not claim universal model compatibility or
  non-bypassability without independent validation.
- Document control limitations and external validation needs.

## 11. Accountability

The project owner approves this policy, reviews exceptions,
assigns security responsibilities, and authorizes releases.

Policy adoption and technical enforcement must be verified
separately. Publishing this document alone does not prove
that repository protections or release controls are active.

## Governing Principle

Veridian must secure the process through which Veridian
itself is built, tested, reviewed, and released.

Don't chase models. Govern action.
