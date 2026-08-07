"""
DecisionAssure Reference Demonstration

This script demonstrates the governance flow from
human request through admissibility.

Execution components (Diya, MIRA, AFS, BIL)
are represented by placeholders for now.
"""

from decisionassure.decision_object import create_decision_object
from decisionassure.governance_receipt import create_governance_receipt
from decisionassure.responsibility_chain import create_responsibility_chain
from decisionassure.decision_replay import replay_decision
from decisionassure.admissibility import evaluate_admissibility

from bvp.boundary_receipt import create_boundary_receipt


print("=" * 60)
print("VERIDIAN REFERENCE IMPLEMENTATION")
print("=" * 60)

#
# Human submits request
#

decision = create_decision_object(
    requestor="human-001",
    authority="Risk Committee",
    responsible_party="Alice",
    policy_version="policy-v1",
    intent="Approve controlled deployment",
    evidence_references=[
        "evidence-001",
        "risk-review-001"
    ],
    decision="APPROVED",
    intended_action="DEPLOY",
    intended_state={
        "status": "ACTIVE"
    },
)

print("\n✓ Decision created")

#
# Governance Receipt
#

governance_receipt = create_governance_receipt(decision)

print("✓ Governance Receipt created")

#
# Responsibility Chain
#

responsibility_chain = create_responsibility_chain(
    organization="Acme Corp",
    business_owner="Alice",
    decision_authority="Risk Committee",
    delegated_by="Alice",
    delegated_to="Veridian",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Deployment Agent",
)

print("✓ Responsibility Chain created")

#
# Boundary Receipt
#

artifact = decision.to_dict()

boundary_receipt = create_boundary_receipt(
    sender="DecisionAssure",
    receiver="Diya",
    artifact_type="GOVERNANCE_DECISION",
    artifact=artifact,
    policy_version="policy-v1",
)

print("✓ Boundary Receipt created")

#
# Replay
#

replay_result = replay_decision(
    decision,
    governance_receipt,
    responsibility_chain,
    boundary_receipt,
    artifact,
)

print("✓ Replay:", replay_result.passed)

#
# Admissibility
#

admissibility = evaluate_admissibility(
    decision=decision,
    replay_result=replay_result,
    reviewer="independent-verifier",
    required_evidence=[
        "evidence-001",
        "risk-review-001"
    ],
)

print("✓ Admissibility:", admissibility.result)

#
# Placeholder for remaining Veridian chain
#

print("\n----- EXECUTION PIPELINE -----")

print("DecisionAssure  -> COMPLETE")
print("BVP             -> VERIFIED")

print("Diya            -> READY")
print("BIL Intent      -> PENDING")

print("Executor        -> PENDING")

print("MIRA            -> PENDING")
print("BIL State       -> PENDING")

print("AFS             -> PENDING")
print("BIL Commit      -> PENDING")

print("State Store     -> PENDING")

print("\nReference demonstration completed.")
