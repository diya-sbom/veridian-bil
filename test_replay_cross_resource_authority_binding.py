from decisionassure.decision_replay import replay_denied_decision

from test_cross_resource_authority_binding import (
    wrong_resource_decision,
    wrong_resource_gov,
    wrong_resource_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time,
    trusted_key_registry,
)

result = replay_denied_decision(
    decision=wrong_resource_decision,
    governance_receipt=wrong_resource_gov,
    responsibility_chain=responsibility_chain,
    boundary_receipt=wrong_resource_boundary,
    boundary_artifact=wrong_resource_decision.to_dict(),
    authority_evidence=authority_evidence,
    authority_boundary_receipt=authority_boundary_receipt,
    authority_state_evidence=authority_state_evidence,
    authority_state_boundary_receipt=authority_state_boundary_receipt,
    execution_time=execution_time,
    expected_failed_condition="RESOURCE_OUT_OF_SCOPE",
    trusted_key_registry=trusted_key_registry,
)

print("CROSS-RESOURCE AUTHORITY DENIAL REPLAY:", result.to_dict())

assert result.passed is True
assert (
    result.message
    == "Authority denial independently reproduced: RESOURCE_OUT_OF_SCOPE"
)

print(
    "PASS: replay independently proved cross-resource "
    "delegated authority violation"
)
