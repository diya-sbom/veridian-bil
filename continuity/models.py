from dataclasses import dataclass
from typing import Dict


@dataclass
class BILRecord:
    record_id: str
    record_type: str
    previous_hash: str
    current_hash: str
    timestamp: str
    payload: Dict


@dataclass
class VerificationResult:
    passed: bool
    message: str
    failed_record: str = ""
