from decisionassure.authority_delegation import create_authority_delegation_evidence
from decisionassure.responsibility_chain import create_responsibility_chain
from bvp.boundary_receipt import create_boundary_receipt


def create_valid_authority_fixture(
    organization="Acme Corp",
    business_owner="Alice",
    decision_authority="Risk Committee",
    delegated_by="Alice",
    delegated_to="Veridian",
    authority_scope="Production Deployment",
    policy_version="policy-v1",
    ai_system="Veridian",
    agent="Deployment Agent",
    policy_reference="policy-ref-001",
    evidence_reference="authority-evidence-001",
    authority_evidence_source="AuthorityService",
):
    responsibility_chain = create_responsibility_chain(
        organization=organization,
        business_owner=business_owner,
        decision_authority=decision_authority,
        delegated_by=delegated_by,
        delegated_to=delegated_to,
        authority_scope=authority_scope,
        policy_version=policy_version,
        ai_system=ai_system,
        agent=agent,
        policy_reference=policy_reference,
        evidence_reference=evidence_reference,
        authority_evidence_source=authority_evidence_source,
    )

    authority_evidence = create_authority_delegation_evidence(
        delegator=delegated_by,
        delegatee=delegated_to,
        authority_scope=authority_scope,
        policy_version=policy_version,
        policy_reference=policy_reference,
        evidence_reference=evidence_reference,
        delegation_status="AUTHORIZED",
    )

    authority_boundary_receipt = create_boundary_receipt(
        sender=authority_evidence_source,
        receiver="Veridian",
        artifact_type="AUTHORITY_DELEGATION",
        artifact=authority_evidence.to_dict(),
        policy_version=policy_version,
    )

    return (
        responsibility_chain,
        authority_evidence,
        authority_boundary_receipt,
    )
