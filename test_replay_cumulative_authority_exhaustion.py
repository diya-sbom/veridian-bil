from decisionassure.decision_replay import replay_denied_decision

from test_cumulative_authority_exhaustion import (
    exhausted_decision,
    exhausted_gov,
    exhausted_boundary,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time,
)

result = replay_denied_decision(
    decision=exhausted_decision,
    governance_receipt=exhausted_gov,
    responsibility_chain=responsibility_chain,
    boundary_receipt=exhausted_boundary,
    boundary_artifact=exhausted_decision.to_dict(),
    authority_evidence=authority_evidence,
    authority_boundary_receipt=authority_boundary_receipt,
    authority_state_evidence=authority_state_evidence,
    authority_state_boundary_receipt=authority_state_boundary_receipt,
    execution_time=execution_time,
    expected_failed_condition="CUMULATIVE_AUTHORITY_EXHAUSTED",
)

print("CUMULATIVE AUTHORITY DENIAL REPLAY:", result.to_dict())

assert result.passed is True
assert (
    result.message
    == "Authority denial independently reproduced: "
       "CUMULATIVE_AUTHORITY_EXHAUSTED"
)

print(
    "PASS: replay independently proved cumulative delegated "
    "authority exhaustion"
)
