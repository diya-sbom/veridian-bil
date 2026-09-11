from dataclasses import asdict, dataclass
from hashlib import sha256
import json


VALID_DELEGATION_STATUSES = {
    "AUTHORIZED",
    "DENIED",
}


@dataclass(frozen=True)
class AuthorityDelegationEvidence:
    evidence_hash: str
    delegator: str
    delegatee: str
    authority_scope: str
    policy_version: str
    policy_reference: str
    evidence_reference: str
    delegation_status: str

    def to_dict(self):
        return asdict(self)


def create_authority_delegation_evidence(
    delegator: str,
    delegatee: str,
    authority_scope: str,
    policy_version: str,
    policy_reference: str,
    evidence_reference: str,
    delegation_status: str,
) -> AuthorityDelegationEvidence:
    if delegation_status not in VALID_DELEGATION_STATUSES:
        raise ValueError(
            "delegation_status must be one of: "
            f"{sorted(VALID_DELEGATION_STATUSES)}"
        )

    payload = {
        "delegator": delegator,
        "delegatee": delegatee,
        "authority_scope": authority_scope,
        "policy_version": policy_version,
        "policy_reference": policy_reference,
        "evidence_reference": evidence_reference,
        "delegation_status": delegation_status,
    }

    evidence_hash = sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return AuthorityDelegationEvidence(
        evidence_hash=evidence_hash,
        delegator=delegator,
        delegatee=delegatee,
        authority_scope=authority_scope,
        policy_version=policy_version,
        policy_reference=policy_reference,
        evidence_reference=evidence_reference,
        delegation_status=delegation_status,
    )


def verify_authority_delegation_evidence(
    evidence: AuthorityDelegationEvidence,
) -> bool:
    payload = {
        "delegator": evidence.delegator,
        "delegatee": evidence.delegatee,
        "authority_scope": evidence.authority_scope,
        "policy_version": evidence.policy_version,
        "policy_reference": evidence.policy_reference,
        "evidence_reference": evidence.evidence_reference,
        "delegation_status": evidence.delegation_status,
    }

    recomputed_hash = sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return recomputed_hash == evidence.evidence_hash
