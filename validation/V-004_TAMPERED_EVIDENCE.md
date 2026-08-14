# V-004 — Tampered Evidence Detection

## Validation Question

Can post-issuance tampering of governance evidence be independently detected and rejected during replay?

## Frozen Baseline

Veridian v1.0.0

## Objective

Determine whether the replay verifier detects modification of evidence after a valid state receipt has been issued.

## Test Method

Begin with a complete governance evidence chain that independently replays as VERIFIED.

Create a copy of the valid state receipt and modify only the embedded state:

`status` → `TAMPERED`

Preserve the original:

- state receipt ID
- execution ID
- state hash
- verification status
- signature

Submit the tampered receipt to the replay verifier.

## Expected Result

FAIL-CLOSED

The verifier must independently recompute integrity information and reject evidence whose contents no longer match its recorded cryptographic evidence.

## Security Requirement

The presence of a receipt must not be treated as proof that the receipt remains authentic.

Post-issuance modification of protected evidence must invalidate replay verification.

## Independence Requirement

Detection must result from reconstruction and verification of the supplied evidence, not from trusting a previously stored VERIFIED status.

## Observed Result

- Untampered baseline replay returned `VERIFIED`.
- State receipt remained present.
- Embedded state was deliberately modified after receipt creation.
- Recorded state hash and signature were not regenerated.
- `state_receipt_hash` failed verification.
- `state_receipt_signature` failed verification.
- `passed` returned `False`.
- `status` returned `FAILED_CLOSED`.

## Status

PASSED

## Conclusion

Veridian independently detected post-issuance modification of state evidence and failed closed.

A governance receipt that exists but whose protected contents have been altered is not accepted as valid evidence.
