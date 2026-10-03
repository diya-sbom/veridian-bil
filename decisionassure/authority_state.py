from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json


VALID_AUTHORITY_STATES = {
    "ACTIVE",
    "SUSPENDED",
    "REVOKED",
    "TRANSFERRED",
}


@dataclass(frozen=True)
class AuthorityStateEvidence:
    """
    Evidence record describing the current state of a delegated authority.

    Supports:
    - deterministic integrity checking of the recorded authority-state fields;
    - binding the state to the exact authority-delegation evidence;
    - comparison of state, scope, delegatee, and policy at execution time;
    - binding to external Boundary Receipt evidence identifying the expected source.

    Assumes:
    - the configured authority-state evidence source is trusted for the claim
      it supplies;
    - authority_evidence_hash identifies the intended delegation evidence;
    - state_reference identifies the governing state-change record.

    Does not by itself establish:
    - that the recorded state is truthful merely because its hash verifies;
    - that the source was authorized to revoke, suspend, or transfer authority;
    - whether the state was effective at a particular execution time;
    - whether the intended action is within delegated scope.

    Hash verification proves integrity of this record, not current authority.
    """

    evidence_hash: str
    authority_evidence_hash: str
    delegatee: str
    authority_scope: str
    policy_version: str
    state: str
    effective_at: str
    state_reference: str

    def to_dict(self):
        return asdict(self)


def create_authority_state_evidence(
    authority_evidence_hash: str,
    delegatee: str,
    authority_scope: str,
    policy_version: str,
    state: str,
    effective_at: str,
    state_reference: str,
) -> AuthorityStateEvidence:
    if state not in VALID_AUTHORITY_STATES:
        raise ValueError(
            "state must be one of: "
            f"{sorted(VALID_AUTHORITY_STATES)}"
        )

    try:
        parsed_effective_at = datetime.fromisoformat(
            effective_at.replace("Z", "+00:00")
        )
    except ValueError:
        raise ValueError("effective_at must be a valid ISO-8601 timestamp")

    if (
        parsed_effective_at.tzinfo is None
        or parsed_effective_at.utcoffset() is None
    ):
        raise ValueError("effective_at must be timezone-aware")

    payload = {
        "authority_evidence_hash": authority_evidence_hash,
        "delegatee": delegatee,
        "authority_scope": authority_scope,
        "policy_version": policy_version,
        "state": state,
        "effective_at": effective_at,
        "state_reference": state_reference,
    }

    evidence_hash = sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return AuthorityStateEvidence(
        evidence_hash=evidence_hash,
        authority_evidence_hash=authority_evidence_hash,
        delegatee=delegatee,
        authority_scope=authority_scope,
        policy_version=policy_version,
        state=state,
        effective_at=effective_at,
        state_reference=state_reference,
    )


def verify_authority_state_evidence(
    evidence: AuthorityStateEvidence,
) -> bool:
    payload = {
        "authority_evidence_hash": evidence.authority_evidence_hash,
        "delegatee": evidence.delegatee,
        "authority_scope": evidence.authority_scope,
        "policy_version": evidence.policy_version,
        "state": evidence.state,
        "effective_at": evidence.effective_at,
        "state_reference": evidence.state_reference,
    }

    recomputed_hash = sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return recomputed_hash == evidence.evidence_hash
