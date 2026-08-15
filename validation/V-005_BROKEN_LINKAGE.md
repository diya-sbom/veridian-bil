# V-005 — Broken Evidence Linkage

## Validation Question

Can Veridian independently detect and reject a governance evidence chain when required evidence exists but its linkage to preceding evidence has been altered?

## Frozen Baseline

Veridian v1.0.0

## Objective

Determine whether the replay verifier rejects an otherwise complete governance evidence chain when a protected linkage between records is broken.

## Expected Result

FAIL-CLOSED

The verifier must not return VERIFIED when evidence records are present but their required relationships cannot be independently established.

## Security Requirement

Evidence presence alone must not establish chain validity.

A governance record must remain cryptographically authentic and correctly linked to the evidence from which it was derived.

If a protected linkage is altered after record creation, replay verification must fail closed.

## Independence Requirement

The verifier must reconstruct and verify relationships from the supplied governance evidence rather than trusting record presence or a previously stored verification result.

## Test Method

A valid end-to-end governance chain was first generated.

The `state_record.state_receipt_id` was then deliberately changed to `BROKEN-LINKAGE` after creation of the signed state record.

The original state receipt remained present.

No verifier logic was modified for the test.

## Observed Result

- Untampered baseline replay returned `VERIFIED`.
- Required governance evidence remained present.
- `state_record.state_receipt_id` was deliberately altered.
- `state_record_signature` returned `FAIL`.
- `state_record_linkage` returned `FAIL`.
- `passed` returned `False`.
- `status` returned `FAILED_CLOSED`.
- Downstream commit and state-store linkage checks remained valid.
- A subsequent untouched baseline replay again returned `VERIFIED`.

## Status

PASSED

## Conclusion

Veridian independently detected a broken relationship between the state record and its originating state receipt and failed closed.

The test demonstrates that evidence presence is not sufficient for verification: protected record contents and their required chain relationships must both remain valid.
