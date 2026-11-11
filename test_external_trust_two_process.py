
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from bvp.trust_root import public_key_id, sign_payload


def main():
    issuer = "ExternalProofIssuer"
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    payload = {
        "action": "DEPLOY",
        "resource": "service-A",
        "decision": "AUTHORIZED",
    }

    key_id = public_key_id(public_key)

    evidence = {
        "issuer": issuer,
        "key_id": key_id,
        "payload": payload,
        "signature": sign_payload(private_key, payload),
    }

    approved_trust = {
        "issuer": issuer,
        "key_id": key_id,
        "public_key_base64": base64.b64encode(
            public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        ).decode("ascii"),
        "revoked": False,
    }

    verifier_code = r"""
import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def main():
    try:
        evidence = json.loads(Path(sys.argv[1]).read_text())
        trust = json.loads(Path(sys.argv[2]).read_text())

        if trust["revoked"] is not False:
            raise ValueError("Revoked key")

        if evidence["issuer"] != trust["issuer"]:
            raise ValueError("Unknown issuer")

        if evidence["key_id"] != trust["key_id"]:
            raise ValueError("Untrusted key")

        raw_key = base64.b64decode(
            trust["public_key_base64"],
            validate=True,
        )

        if hashlib.sha256(raw_key).hexdigest() != trust["key_id"]:
            raise ValueError("Incorrect key ID")

        public_key = Ed25519PublicKey.from_public_bytes(raw_key)

        message = json.dumps(
            evidence["payload"],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        signature = base64.b64decode(
            evidence["signature"],
            validate=True,
        )

        public_key.verify(signature, message)

    except (InvalidSignature, ValueError, KeyError, TypeError, IndexError):
        print("FAILED_CLOSED")
        return 1

    print("SIGNATURE_VERIFIED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)

        evidence_path = root / "evidence.json"
        trust_path = root / "approved_trust.json"
        verifier_path = root / "verifier.py"

        verifier_path.write_text(verifier_code)

        def verify(evidence_object, trust_object):
            evidence_path.write_text(json.dumps(evidence_object))
            trust_path.write_text(json.dumps(trust_object))

            return subprocess.run(
                [
                    sys.executable,
                    str(verifier_path),
                    str(evidence_path),
                    str(trust_path),
                ],
                capture_output=True,
                text=True,
            )

        result = verify(evidence, approved_trust)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "SIGNATURE_VERIFIED"
        print("PASS: Separately provisioned trusted key accepted")

        tampered = json.loads(json.dumps(evidence))
        tampered["payload"]["resource"] = "service-B"

        result = verify(tampered, approved_trust)
        assert result.returncode != 0
        assert result.stdout.strip() == "FAILED_CLOSED"
        print("PASS: Tampered evidence rejected")

        unknown = dict(approved_trust)
        unknown["issuer"] = "UnknownIssuer"

        result = verify(evidence, unknown)
        assert result.returncode != 0
        assert result.stdout.strip() == "FAILED_CLOSED"
        print("PASS: Unknown issuer rejected")

        revoked = dict(approved_trust)
        revoked["revoked"] = True

        result = verify(evidence, revoked)
        assert result.returncode != 0
        assert result.stdout.strip() == "FAILED_CLOSED"
        print("PASS: Revoked key rejected")

    print("PASS: TWO-PROCESS TRUST REGRESSION")


if __name__ == "__main__":
    main()
