# V-008 — Cross-Process Evidence Replay

## Objective

Verify that a completed Veridian evidence chain can be persisted,
loaded by a separate Python process, reconstructed, and independently
verified without relying on the original in-memory objects.

## Procedure

1. Execute the canonical Veridian governance and execution chain.
2. Serialize the resulting evidence artifacts to:
   `validation/v008_evidence_bundle.json`
3. Terminate the producer process.
4. Start a separate consumer process.
5. Load the persisted evidence bundle from disk.
6. Reconstruct the evidence objects.
7. Submit the reconstructed artifacts to `verify_chain()`.
8. Require every verification check to pass.

## Result

All replay verification checks passed.

Final verifier status:

`VERIFIED`

Final test result:

`V-008 RESULT: PASSED`

## Security Property Demonstrated

Veridian replay verification does not require the original
in-memory execution objects.

Persisted evidence can cross a process boundary, be reconstructed,
and remain independently verifiable by the replay verifier.

This demonstrates portable evidence verification across process
boundaries.

## Status

PASS
