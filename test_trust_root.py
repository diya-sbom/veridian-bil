from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.trust_root import (
    TrustedKeyRegistry,
    sign_payload,
)


issuer = "AuthorityService"

private_key = Ed25519PrivateKey.generate()
public_key = private_key.public_key()

registry = TrustedKeyRegistry()
key_id = registry.register(issuer, public_key)

payload = {
    "sender": issuer,
    "receiver": "Veridian",
    "artifact_type": "AUTHORITY_DELEGATION",
    "artifact_hash": "abc123",
    "policy_version": "policy-v1",
}

signature = sign_payload(private_key, payload)

# CASE 1: trusted issuer + valid signature
assert registry.verify(
    issuer,
    key_id,
    payload,
    signature,
) is True

print("PASS: trusted issuer with valid signature accepted")


# CASE 2: payload tampering
tampered_payload = dict(payload)
tampered_payload["policy_version"] = "policy-v999"

assert registry.verify(
    issuer,
    key_id,
    tampered_payload,
    signature,
) is False

print("PASS: tampered payload denied")


# CASE 3: unknown issuer
assert registry.verify(
    "UnknownAuthority",
    key_id,
    payload,
    signature,
) is False

print("PASS: unknown issuer denied")


# CASE 4: unknown key
assert registry.verify(
    issuer,
    "unknown-key-id",
    payload,
    signature,
) is False

print("PASS: unknown key denied")


# CASE 5: revoked trusted key
registry.revoke(issuer, key_id)

assert registry.verify(
    issuer,
    key_id,
    payload,
    signature,
) is False

print("PASS: revoked trusted key denied")


print("PASS: trust root fails closed")
