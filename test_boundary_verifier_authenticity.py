from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.boundary_receipt import create_boundary_receipt
from bvp.trust_root import (
    TrustedKeyRegistry,
    authenticate_boundary_receipt,
)
from bvp.verify_boundary import verify_boundary_receipt


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


# CASE 1: legacy behavior remains valid by default
legacy_result = verify_boundary_receipt(
    receipt,
    artifact,
    expected_sender=issuer,
    expected_receiver="Veridian",
    expected_artifact_type="AUTHORITY_DELEGATION",
    expected_policy_version="policy-v1",
)

assert legacy_result.passed is True
print("PASS: legacy verification remains compatible")


# CASE 2: unsigned receipt fails when authenticity is required
unsigned_required = verify_boundary_receipt(
    receipt,
    artifact,
    expected_sender=issuer,
    expected_receiver="Veridian",
    expected_artifact_type="AUTHORITY_DELEGATION",
    expected_policy_version="policy-v1",
    trusted_key_registry=registry,
    require_authenticity=True,
)

assert unsigned_required.passed is False
assert unsigned_required.failed_field == "issuer_signature"

print("PASS: unsigned receipt denied when authenticity required")


# CASE 3: trusted signed receipt passes
signed_receipt = authenticate_boundary_receipt(
    receipt,
    private_key,
)

signed_result = verify_boundary_receipt(
    signed_receipt,
    artifact,
    expected_sender=issuer,
    expected_receiver="Veridian",
    expected_artifact_type="AUTHORITY_DELEGATION",
    expected_policy_version="policy-v1",
    trusted_key_registry=registry,
    require_authenticity=True,
)

assert signed_result.passed is True
print("PASS: trusted signed receipt accepted")


# CASE 4: authenticity cannot be required without a trust root
missing_registry = verify_boundary_receipt(
    signed_receipt,
    artifact,
    expected_sender=issuer,
    expected_receiver="Veridian",
    expected_artifact_type="AUTHORITY_DELEGATION",
    expected_policy_version="policy-v1",
    require_authenticity=True,
)

assert missing_registry.passed is False
assert missing_registry.failed_field == "trusted_key_registry"

print("PASS: missing trust root denied")


# CASE 5: revoked signer fails verification
registry.revoke(issuer, key_id)

revoked_result = verify_boundary_receipt(
    signed_receipt,
    artifact,
    expected_sender=issuer,
    expected_receiver="Veridian",
    expected_artifact_type="AUTHORITY_DELEGATION",
    expected_policy_version="policy-v1",
    trusted_key_registry=registry,
    require_authenticity=True,
)

assert revoked_result.passed is False
assert revoked_result.failed_field == "issuer_authenticity"

print("PASS: revoked signer denied by boundary verifier")

print("PASS: BoundaryReceipt verifier trust-root modes enforced")
