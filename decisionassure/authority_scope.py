AUTHORITY_SCOPE_ACTION_MAP = {
    "Production Deployment": {"DEPLOY"},
}


def is_action_authorized(authority_scope: str, intended_action: str) -> bool:
    """
    Deterministically determine whether an authority scope permits an action.

    Unknown scopes and unknown actions fail closed.
    """
    allowed_actions = AUTHORITY_SCOPE_ACTION_MAP.get(authority_scope)

    if allowed_actions is None:
        return False

    return intended_action in allowed_actions
