from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from decisionassure.decision_object import DecisionObject


@dataclass(frozen=True)
class GovernanceReceipt:
    receipt_hash: str
    decision_id: str
    policy_version: str
    authority: str
    decision: str

    def to_dict(self):
        return asdict(self)


def create_governance_receipt(decision: DecisionObject):

    payload = {
        "decision_id": decision.decision_id,
        "authority": decision.authority,
        "policy_version": decision.policy_version,
        "decision": decision.decision,
        "intent": decision.intent,
    }

    receipt_hash = sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    return GovernanceReceipt(
        receipt_hash=receipt_hash,
        decision_id=decision.decision_id,
        policy_version=decision.policy_version,
        authority=decision.authority,
        decision=decision.decision,
    )
