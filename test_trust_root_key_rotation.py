from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.boundary_receipt import create_boundary_receipt
from bvp.trust_root import (
    TrustedKeyRegistry,
    authenticate_boundary_receipt,
    verify_boundary_receipt_authenticity,
)

issuer = "AuthorityService"

artifact = {
    "authority_scope": "Production Deployment",
    "policy_version": "policy-v1",
}

# Old trusted key.
old_private_key = Ed25519PrivateKey.generate()
old_public_key = old_private_key.public_key()

registry = TrustedKeyRegistry()
old_key_id = registry.register(issuer, old_public_key)

old_receipt = create_boundary_receipt(
    sender=issuer,
    receiver="Veridian",
    artifact_type="AUTHORITY_DELEGATION",
    artifact=artifact,
    policy_version="policy-v1",
)

old_signed_receipt = authenticate_boundary_receipt(
    old_receipt,
    old_private_key,
)

assert verify_boundary_receipt_authenticity(
    old_signed_receipt,
    registry,
) is True

print("PASS: old trusted key accepted before rotation")

# Rotate to a new key.
new_private_key = Ed25519PrivateKey.generate()
new_public_key = new_private_key.public_key()
new_key_id = registry.register(issuer, new_public_key)

assert new_key_id != old_key_id

# Revoke the old key after the new key is trusted.
registry.revoke(issuer, old_key_id)

# The old signature is still cryptographically intact,
# but the old key is no longer trusted.
assert verify_boundary_receipt_authenticity(
    old_signed_receipt,
    registry,
) is False

print("PASS: old signed receipt denied after key rotation")

# New key signs an equivalent receipt.
new_receipt = create_boundary_receipt(
    sender=issuer,
    receiver="Veridian",
    artifact_type="AUTHORITY_DELEGATION",
    artifact=artifact,
    policy_version="policy-v1",
)

new_signed_receipt = authenticate_boundary_receipt(
    new_receipt,
    new_private_key,
)

assert verify_boundary_receipt_authenticity(
    new_signed_receipt,
    registry,
) is True

print("PASS: new trusted key accepted after rotation")
print("PASS: key rotation does not preserve authority through a revoked signing key")
