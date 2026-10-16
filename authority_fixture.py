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
    governed_resource=None,
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
        governed_resource=governed_resource,
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


def create_trusted_authority_fixture(
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
    governed_resource=None,
    trusted_key_registry=None,
    signing_key=None,
):
    """
    Create the normal authority fixture, then authenticate its
    AUTHORITY_DELEGATION Boundary Receipt with a trusted Ed25519 key.

    Existing create_valid_authority_fixture() semantics remain unchanged.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    from bvp.trust_root import (
        TrustedKeyRegistry,
        authenticate_boundary_receipt,
    )

    (
        responsibility_chain,
        authority_evidence,
        authority_boundary_receipt,
    ) = create_valid_authority_fixture(
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
        governed_resource=governed_resource,
    )

    if trusted_key_registry is None:
        trusted_key_registry = TrustedKeyRegistry()

    if signing_key is None:
        signing_key = Ed25519PrivateKey.generate()

    trusted_key_registry.register(
        authority_evidence_source,
        signing_key.public_key(),
    )

    authority_boundary_receipt = authenticate_boundary_receipt(
        authority_boundary_receipt,
        signing_key,
    )

    return (
        responsibility_chain,
        authority_evidence,
        authority_boundary_receipt,
        trusted_key_registry,
    )
