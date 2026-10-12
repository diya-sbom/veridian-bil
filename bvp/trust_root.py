from __future__ import annotations

import base64
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Dict

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from bvp.boundary_receipt import canonical_json


def public_key_id(public_key: Ed25519PublicKey) -> str:
    """
    Derive a deterministic identifier from an Ed25519 public key.
    """
    raw_key = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return sha256(raw_key).hexdigest()


def sign_payload(
    private_key: Ed25519PrivateKey,
    payload: Dict[str, Any],
) -> str:
    """
    Sign the canonical representation of a payload.
    """
    message = canonical_json(payload).encode("utf-8")
    signature = private_key.sign(message)
    return base64.b64encode(signature).decode("ascii")


def verify_payload_signature(
    public_key: Ed25519PublicKey,
    payload: Dict[str, Any],
    signature: str,
) -> bool:
    """
    Verify an Ed25519 signature over a canonical payload.
    """
    try:
        signature_bytes = base64.b64decode(
            signature.encode("ascii"),
            validate=True,
        )
        message = canonical_json(payload).encode("utf-8")
        public_key.verify(signature_bytes, message)
        return True
    except (InvalidSignature, ValueError):
        return False


@dataclass
class TrustedKeyRegistry:
    """
    Explicit trust root for receipt/evidence issuers.

    A cryptographically valid signature is insufficient by itself.
    The issuer and key must also be explicitly trusted and not revoked.
    """

    _trusted_keys: Dict[str, Dict[str, Ed25519PublicKey]] = field(
        default_factory=dict
    )
    _revoked_keys: set[tuple[str, str]] = field(default_factory=set)

    def register(
        self,
        issuer: str,
        public_key: Ed25519PublicKey,
    ) -> str:
        if not isinstance(issuer, str) or not issuer.strip():
            raise ValueError("issuer must be a non-empty string")

        key_id = public_key_id(public_key)

        self._trusted_keys.setdefault(issuer, {})[key_id] = public_key
        self._revoked_keys.discard((issuer, key_id))

        return key_id

    def revoke(
        self,
        issuer: str,
        key_id: str,
    ) -> None:
        self._revoked_keys.add((issuer, key_id))

    def verify(
        self,
        issuer: str,
        key_id: str,
        payload: Dict[str, Any],
        signature: str,
    ) -> bool:
        if (issuer, key_id) in self._revoked_keys:
            return False

        issuer_keys = self._trusted_keys.get(issuer)
        if issuer_keys is None:
            return False

        public_key = issuer_keys.get(key_id)
        if public_key is None:
            return False

        return verify_payload_signature(
            public_key,
            payload,
            signature,
        )


def authenticate_boundary_receipt(
    receipt,
    private_key: Ed25519PrivateKey,
):
    """
    Authenticate an already-created BoundaryReceipt.

    The existing receipt hash remains the integrity anchor.
    Ed25519 authenticates that completed hash.
    """
    from dataclasses import replace

    key_id = public_key_id(private_key.public_key())

    signature = sign_payload(
        private_key,
        {
            "current_receipt_hash": receipt.current_receipt_hash,
        },
    )

    return replace(
        receipt,
        issuer_key_id=key_id,
        issuer_signature=signature,
    )


def verify_boundary_receipt_authenticity(
    receipt,
    registry: TrustedKeyRegistry,
) -> bool:
    """
    Verify that a BoundaryReceipt was authenticated by a currently
    trusted key belonging to its claimed sender.
    """
    if receipt.issuer_key_id is None or receipt.issuer_signature is None:
        return False

    return registry.verify(
        receipt.sender,
        receipt.issuer_key_id,
        {
            "current_receipt_hash": receipt.current_receipt_hash,
        },
        receipt.issuer_signature,
    )
