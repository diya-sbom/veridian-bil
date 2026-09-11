from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


@dataclass(frozen=True)
class ResponsibilityChain:
    """
    Preserves accountability across governance delegation.
    """

    chain_id: str
    delegation_time: str

    organization: str
    business_owner: str
    decision_authority: str

    delegated_by: str
    delegated_to: str

    authority_scope: str
    policy_version: str

    ai_system: str
    agent: str
    sub_agent: Optional[str]
    valid_until: Optional[str]
    policy_reference: Optional[str]
    evidence_reference: Optional[str]
    authority_evidence_source: Optional[str]

    def to_dict(self):
        return asdict(self)


def create_responsibility_chain(
    organization: str,
    business_owner: str,
    decision_authority: str,
    delegated_by: str,
    delegated_to: str,
    authority_scope: str,
    policy_version: str,
    ai_system: str,
    agent: str,
    sub_agent: Optional[str] = None,
    valid_until: Optional[str] = None,
    policy_reference: Optional[str] = None,
    evidence_reference: Optional[str] = None,
    authority_evidence_source: Optional[str] = None,
):

    return ResponsibilityChain(
        chain_id=str(uuid4()),
        delegation_time=datetime.now(timezone.utc).isoformat(),

        organization=organization,
        business_owner=business_owner,
        decision_authority=decision_authority,

        delegated_by=delegated_by,
        delegated_to=delegated_to,

        authority_scope=authority_scope,
        policy_version=policy_version,

        ai_system=ai_system,
        agent=agent,
        sub_agent=sub_agent,
        valid_until=valid_until,
        policy_reference=policy_reference,
        evidence_reference=evidence_reference,
        authority_evidence_source=authority_evidence_source,
    )
