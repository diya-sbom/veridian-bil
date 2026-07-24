# Decision Object

## Purpose

A Decision Object is the complete, verifiable record of a governance decision.

It captures not only the final decision but also the authority, evidence, policy, responsibility, execution, and resulting outcome.

## Required Fields

- Decision ID
- Timestamp
- Decision Authority
- Responsible Party
- Policy Version
- Evidence References
- Decision Result
- Reasoning Summary
- Intended Action
- Intended State Change

## Post-Execution Fields

- Actual Action
- Actual State Change
- Execution Time
- Verification Result
- Commit Status

## Verification

A Decision Object must allow an independent reviewer to answer:

- Who made the decision?
- Under what authority?
- Based on which evidence?
- Which policy was applied?
- What action was approved?
- What actually happened?
- Did the outcome remain within the approved scope?

## Integrity

A Decision Object is immutable after commitment.

Any modification creates a new Decision Object with its own identity.

## Goal

Every significant autonomous decision becomes independently verifiable, replayable, and admissible.
