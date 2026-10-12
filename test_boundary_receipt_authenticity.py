from dataclasses import replace

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.boundary_receipt import create_boundary_receipt
from bvp.trust_root import (
    TrustedKeyRegistry,
    authenticate_boundary_receipt,
    verify_boundary_receipt_authenticity,
)


issuer = "AuthorityService"

private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

registry = TrustedKeyRegistry()
key_id = registry.register(issuer, public_key)

artifact = {
    "authority_scope": "Production Deployment",
    "policy_version": "policy-v1",
}

receipt = create_boundary_receipt(
    sender=issuer,
    receiver="Veridian",
    artifact_type="AUTHORITY_DELEGATION",
    artifact=artifact,
    policy_version="policy-v1",
)

# CASE 1: legacy unsigned receipt makes no authenticity claim
assert verify_boundary_receipt_authenticity(
    receipt,
    registry,
) is False

print("PASS: unsigned legacy receipt not treated as authenticated")


# CASE 2: trusted signer authenticates completed receipt hash
signed_receipt = authenticate_boundary_receipt(
    receipt,
    private_key,
)

assert signed_receipt.issuer_key_id == key_id
assert signed_receipt.issuer_signature is not None
assert verify_boundary_receipt_authenticity(
    signed_receipt,
    registry,
) is True

print("PASS: trusted signed BoundaryReceipt authenticated")


# CASE 3: mutate the signed receipt hash after signing
tampered_receipt = replace(
    signed_receipt,
    current_receipt_hash="0" * 64,
)

assert verify_boundary_receipt_authenticity(
    tampered_receipt,
    registry,
) is False

print("PASS: changed receipt hash denied")


# CASE 4: same key is not trusted for a different claimed sender
wrong_sender_receipt = replace(
    signed_receipt,
    sender="FakeAuthorityService",
)

assert verify_boundary_receipt_authenticity(
    wrong_sender_receipt,
    registry,
) is False

print("PASS: wrong claimed issuer denied")


# CASE 5: revoke signer after authentication
registry.revoke(issuer, key_id)

assert verify_boundary_receipt_authenticity(
    signed_receipt,
    registry,
) is False

print("PASS: revoked BoundaryReceipt signer denied")

print("PASS: BoundaryReceipt authenticity fails closed")
