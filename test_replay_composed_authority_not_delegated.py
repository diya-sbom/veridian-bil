from decisionassure.decision_replay import replay_denied_decision

from test_composed_authority_not_delegated import (
    composed_decision,
    composed_gov,
    composed_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    component_receipts,
)

result = replay_denied_decision(
    decision=composed_decision,
    governance_receipt=composed_gov,
    responsibility_chain=responsibility_chain,
    boundary_receipt=composed_boundary,
    boundary_artifact=composed_decision.to_dict(),
    authority_evidence=authority_evidence,
    authority_boundary_receipt=authority_boundary_receipt,
    authority_state_evidence=authority_state_evidence,
    authority_state_boundary_receipt=authority_state_boundary_receipt,
    execution_time=None,
    expected_failed_condition="COMPOSED_AUTHORITY_NOT_DELEGATED",
    component_intent_receipts=component_receipts,
)

print("COMPOSED AUTHORITY DENIAL REPLAY:", result.to_dict())

assert result.passed is True
assert (
    result.message
    == "Authority denial independently reproduced: "
       "COMPOSED_AUTHORITY_NOT_DELEGATED"
)

print(
    "PASS: replay independently proved composed authority "
    "was not delegated"
)
