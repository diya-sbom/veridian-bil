# V-006 — Invalid Signature Detection

## Objective

Validate that Veridian fails closed when governance evidence contains an invalid cryptographic signature, even when the evidence remains present and its protected state 
content has not been modified.

## Security Requirement

Evidence presence alone must not establish authenticity.

A governance receipt with an invalid signature must not be accepted as valid evidence.

## Independence Requirement

Detection must result from reconstruction and verification of the supplied evidence, not from trusting a previously stored verification result.

## Test Method

A valid end-to-end governance chain was first generated.

The `state_receipt.signature` was then deliberately replaced with `INVALID-SIGNATURE` after creation of the state receipt.

The state receipt remained present.

The protected state and its recorded state hash were not modified.

No verifier logic was modified for the test.

## Observed Result

- `state_receipt_hash` returned `PASS`.
- `state_receipt_signature` returned `FAIL`.
- `state_receipt_linkage` returned `PASS`.
- `state_receipt_verified` returned `PASS`.
- Downstream state-record, commit, and state-store checks remained valid.
- `passed` returned `False`.
- `status` returned `FAILED_CLOSED`.
- `failed_checks` identified `state_receipt_signature`.

## Status

PASSED

## Conclusion

Veridian independently detected an invalid state-receipt signature and failed closed.

The test demonstrates that evidence presence, valid content hashing, valid linkage, and successful downstream processing are not sufficient for verification when the 
evidence itself cannot be cryptographically authenticated.
