HUMAN_APPROVAL_REQUIREMENTS = {
    ("DEPLOY", "production-service-A"),
}


def requires_independent_human_approval(
    intended_action: str,
    governed_resource: str | None,
) -> bool:
    """
    Policy-controlled determination of whether an action/resource pair
    requires independently validated human approval.

    The decision object does not control this requirement.
    """
    if not isinstance(intended_action, str) or not intended_action.strip():
        return False

    if governed_resource is None:
        return False

    if not isinstance(governed_resource, str) or not governed_resource.strip():
        return False

    return (
        intended_action,
        governed_resource,
    ) in HUMAN_APPROVAL_REQUIREMENTS
