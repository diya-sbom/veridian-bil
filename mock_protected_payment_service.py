"""Test-only protected payment service. No network or real payments."""

from datetime import datetime, timezone
from bvp.trust_root import TrustedKeyRegistry


class MockProtectedPaymentService:
    def __init__(self, trusted_registry: TrustedKeyRegistry):
        self.registry = trusted_registry
        self.requests = []
        self.completed = []
        self.used_authorizations = set()

    def execute_payment(
        self, credential, payee, amount, decision_id,
        authorization=None,
    ):
        if credential != "TEST-API-CREDENTIAL":
            return {"status": "FAILED_CLOSED"}

        if not isinstance(authorization, dict):
            return {"status": "FAILED_CLOSED"}

        try:
            issuer = authorization["issuer"]
            key_id = authorization["key_id"]
            signature = authorization["signature"]
            payload = authorization["payload"]

            if not isinstance(payload, dict):
                return {"status": "FAILED_CLOSED"}

            if not self.registry.verify(
                issuer, key_id, payload, signature
            ):
                return {"status": "FAILED_CLOSED"}

            if (
                payload.get("action") != "EXECUTE_PAYMENT"
                or payload.get("payee") != payee
                or payload.get("amount") != amount
                or payload.get("decision_id") != decision_id
                or payload.get("audience") != "MOCK-PAYMENT-SERVICE"
            ):
                return {"status": "FAILED_CLOSED"}

            authorization_id = payload["authorization_id"]
            expires_at = datetime.fromisoformat(payload["expires_at"])

            if (
                not isinstance(authorization_id, str)
                or not authorization_id
                or expires_at.tzinfo is None
                or datetime.now(timezone.utc) >= expires_at
                or authorization_id in self.used_authorizations
            ):
                return {"status": "FAILED_CLOSED"}

        except (KeyError, TypeError, ValueError, AttributeError):
            return {"status": "FAILED_CLOSED"}

        # Authorization is accepted and consumed only here.
        self.used_authorizations.add(authorization_id)

        request = {
            "payee": payee,
            "amount": amount,
            "decision_id": decision_id,
            "authorization_id": authorization_id,
        }

        self.requests.append(request)
        self.completed.append(dict(request))

        return {"status": "COMPLETED", "request": dict(request)}


if __name__ == "__main__":
    service = MockProtectedPaymentService(TrustedKeyRegistry())

    result = service.execute_payment(
        "TEST-API-CREDENTIAL",
        "unauthorized-payee",
        100,
        "NO-VERIDIAN-AUTHORIZATION",
    )

    assert result["status"] == "FAILED_CLOSED"
    assert service.requests == []
    assert service.completed == []

    print("PASS: CREDENTIAL-ONLY PAYMENT REJECTED")
    print("PASS: ZERO UNAUTHORIZED PAYMENTS")
    print("PASS: PROTECTED MOCK SERVICE INITIALIZED")
