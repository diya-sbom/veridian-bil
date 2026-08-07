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
    timestamp: str

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
):

    return ResponsibilityChain(
        chain_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),

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
    )
