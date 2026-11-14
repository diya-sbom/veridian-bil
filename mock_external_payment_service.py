"""Local test-only external payment service. No real network or payments."""

class MockExternalPaymentService:
    def __init__(self):
        self.requests = []
        self.completed = []

    def execute_payment(self, credential, payee, amount, decision_id):
        if credential != "TEST-API-CREDENTIAL":
            raise PermissionError("Invalid test API credential")

        request = {
            "payee": payee,
            "amount": amount,
            "decision_id": decision_id,
        }

        self.requests.append(request)
        self.completed.append(dict(request))
        return {"status": "COMPLETED", "request": dict(request)}


if __name__ == "__main__":
    service = MockExternalPaymentService()

    assert service.requests == []
    assert service.completed == []

    print("PASS: MOCK EXTERNAL PAYMENT SERVICE CREATED")
    print("PASS: NO EXTERNAL REQUESTS OR PAYMENTS")
