"""Versioned binding of an approved decision to its execution parameters."""

from dataclasses import asdict
from hashlib import sha256
import json

BINDING_VERSION = "APPROVAL_DECISION_BINDING_V1"


def decision_binding_digest(decision):
    """Return a versioned digest of the complete governance decision."""
    payload = {
        "binding_version": BINDING_VERSION,
        "decision": asdict(decision),
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
