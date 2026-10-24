from decisionassure.diya_adapter import verify_intent
from decisionassure.intent_receipt import create_intent_receipt
from bil.intent_record import create_intent_record
from executor.executor import execute_intent


def execute_with_current_authority(
    decision,
    governance_receipt,
    boundary_receipt,
    responsibility_chain,
    authority_evidence,
    authority_boundary_receipt,
    authority_state_evidence,
    authority_state_boundary_receipt,
    execution_time,
    trusted_key_registry,
    parent_authority_evidence=None,
    parent_authority_boundary_receipt=None,
    component_intent_receipts=None,
):
    """
    Revalidate authority immediately before execution.

    A previously VERIFIED record is not sufficient by itself.
    Current authority must still permit the action at execution time.
    """

    verification = verify_intent(
        decision,
        governance_receipt,
        boundary_receipt,
        responsibility_chain,
        authority_evidence,
        authority_boundary_receipt,
        authority_state_evidence=authority_state_evidence,
        authority_state_boundary_receipt=authority_state_boundary_receipt,
        execution_time=execution_time,
        parent_authority_evidence=parent_authority_evidence,
        parent_authority_boundary_receipt=parent_authority_boundary_receipt,
        component_intent_receipts=component_intent_receipts,
        trusted_key_registry=trusted_key_registry,
    )

    fresh_intent_receipt = create_intent_receipt(
        boundary_receipt,
        verification,
    )

    fresh_intent_record = create_intent_record(
        governance_receipt,
        boundary_receipt,
        fresh_intent_receipt,
    )

    execution = execute_intent(fresh_intent_record)

    return verification, fresh_intent_receipt, fresh_intent_record, execution
