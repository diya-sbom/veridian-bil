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

    aggregate_limit: int | None = None
    consumed_units: int | None = None
    authority_unit: str | None = None
    def to_dict(self):
        data = asdict(self)
        if self.aggregate_limit is None:
            data.pop("aggregate_limit")
            data.pop("consumed_units")
            data.pop("authority_unit")
        return data


def create_authority_state_evidence(
    authority_evidence_hash: str,
    delegatee: str,
    authority_scope: str,
    policy_version: str,
    state: str,
    effective_at: str,
    state_reference: str,
    aggregate_limit: int | None = None,
    consumed_units: int | None = None,
    authority_unit: str | None = None,
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

    cumulative_values = (
        aggregate_limit,
        consumed_units,
        authority_unit,
    )
    has_any_cumulative = any(value is not None for value in cumulative_values)
    has_all_cumulative = all(value is not None for value in cumulative_values)

    if has_any_cumulative and not has_all_cumulative:
        raise ValueError(
            "cumulative authority fields must be provided together"
        )

    if has_all_cumulative:
        if (
            isinstance(aggregate_limit, bool)
            or not isinstance(aggregate_limit, int)
            or aggregate_limit <= 0
        ):
            raise ValueError("aggregate_limit must be a positive integer")

        if (
            isinstance(consumed_units, bool)
            or not isinstance(consumed_units, int)
            or consumed_units < 0
        ):
            raise ValueError("consumed_units must be a non-negative integer")

        if consumed_units > aggregate_limit:
            raise ValueError("consumed_units cannot exceed aggregate_limit")

        if not isinstance(authority_unit, str) or not authority_unit.strip():
            raise ValueError("authority_unit must be a non-empty string")

    payload = {
        "authority_evidence_hash": authority_evidence_hash,
        "delegatee": delegatee,
        "authority_scope": authority_scope,
        "policy_version": policy_version,
        "state": state,
        "effective_at": effective_at,
        "state_reference": state_reference,
    }

    if aggregate_limit is not None:
        payload.update(
            {
                "aggregate_limit": aggregate_limit,
                "consumed_units": consumed_units,
                "authority_unit": authority_unit,
            }
        )

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
        aggregate_limit=aggregate_limit,
        consumed_units=consumed_units,
        authority_unit=authority_unit,
    )


def verify_authority_state_evidence(
    evidence: AuthorityStateEvidence,
) -> bool:
    cumulative_values = (
        evidence.aggregate_limit,
        evidence.consumed_units,
        evidence.authority_unit,
    )

    has_any_cumulative = any(value is not None for value in cumulative_values)
    has_all_cumulative = all(value is not None for value in cumulative_values)

    if has_any_cumulative and not has_all_cumulative:
        return False

    if has_all_cumulative:
        if (
            isinstance(evidence.aggregate_limit, bool)
            or not isinstance(evidence.aggregate_limit, int)
            or evidence.aggregate_limit <= 0
        ):
            return False

        if (
            isinstance(evidence.consumed_units, bool)
            or not isinstance(evidence.consumed_units, int)
            or evidence.consumed_units < 0
            or evidence.consumed_units > evidence.aggregate_limit
        ):
            return False

        if (
            not isinstance(evidence.authority_unit, str)
            or not evidence.authority_unit.strip()
        ):
            return False

    payload = {
        "authority_evidence_hash": evidence.authority_evidence_hash,
        "delegatee": evidence.delegatee,
        "authority_scope": evidence.authority_scope,
        "policy_version": evidence.policy_version,
        "state": evidence.state,
        "effective_at": evidence.effective_at,
        "state_reference": evidence.state_reference,
    }

    if evidence.aggregate_limit is not None:
        payload.update(
            {
                "aggregate_limit": evidence.aggregate_limit,
                "consumed_units": evidence.consumed_units,
                "authority_unit": evidence.authority_unit,
            }
        )

    recomputed_hash = sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return recomputed_hash == evidence.evidence_hash
