from datetime import datetime, timezone

from bvp.boundary_receipt import create_boundary_receipt
from decisionassure.authority_state import create_authority_state_evidence


def create_authority_state_fixture(
    responsibility_chain,
    authority_evidence,
    state="ACTIVE",
    effective_at=None,
    state_reference="authority-state-001",
    aggregate_limit=None,
    consumed_units=None,
    authority_unit=None,
):
    if effective_at is None:
        effective_at = datetime.now(timezone.utc).isoformat()

    state_evidence = create_authority_state_evidence(
        authority_evidence_hash=authority_evidence.evidence_hash,
        delegatee=authority_evidence.delegatee,
        authority_scope=authority_evidence.authority_scope,
        policy_version=authority_evidence.policy_version,
        state=state,
        effective_at=effective_at,
        state_reference=state_reference,
        aggregate_limit=aggregate_limit,
        consumed_units=consumed_units,
        authority_unit=authority_unit,
    )

    state_boundary_receipt = create_boundary_receipt(
        sender=responsibility_chain.authority_evidence_source,
        receiver="Veridian",
        artifact_type="AUTHORITY_STATE",
        artifact=state_evidence.to_dict(),
        policy_version=responsibility_chain.policy_version,
    )

    return state_evidence, state_boundary_receipt
