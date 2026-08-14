# V-003 — Missing Evidence Detection

## Validation Question

Can an incomplete governance evidence chain be independently detected and rejected?

## Frozen Baseline

Veridian v1.0.0

## Objective

Determine whether the replay verifier refuses to verify a governance chain when required evidence is missing.

## Expected Result

FAIL-CLOSED

The verifier must not return VERIFIED when a required governance record is absent.

## Security Requirement

Missing evidence must not be treated as equivalent to valid evidence.

If any required record necessary to establish intent, execution, state transition, or commit integrity is unavailable, the complete governance chain must fail closed.

## Independence Requirement

The verifier must establish completeness from the supplied governance evidence rather than trusting a previously stored PASS or verification status.

## Status

PASSED

Observed result:

- Required `state_receipt` deliberately removed from an otherwise complete evidence chain.
- Replay verifier detected `missing_state_receipt`.
- `passed` returned `False`.
- `status` returned `FAILED_CLOSED`.
- No incomplete governance chain was accepted as verified.

Conclusion:

Veridian independently detects missing required governance evidence and fails closed rather than trusting an incomplete chain.
