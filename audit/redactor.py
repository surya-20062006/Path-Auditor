import re
import base64
import os
from typing import List, Dict, Any, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from backend.core.config import settings
from backend.core.logger import logger
from backend.core.metrics import PII_REDACTION_COUNTER

try:
    from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False


# Custom regular expressions for Indian & international financial/identity PII
REGEX_PATTERNS = {
    "EMAIL_ADDRESS": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "PHONE_NUMBER": r"(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}",
    "PAN": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",  # Indian Permanent Account Number
    "AADHAAR": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",  # Indian Aadhaar Number
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",  # US Social Security Number
    "CREDIT_CARD": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
    "PASSPORT": r"\b[A-PR-WYa-pr-wy][1-9]\d\s?\d{4}[1-9]\b",
    "BANK_ACCOUNT": r"\b\d{9,18}\b",
}


class PIIRedactor:
    """
    Enterprise PII Redaction Engine with AES-256-GCM encryption of original tokens.
    Uses Microsoft Presidio when available, with comprehensive regex fallback.
    """

    def __init__(self):
        self._key = self._get_aes_key()
        self._aesgcm = AESGCM(self._key)
        self.analyzer = None
        self.anonymizer = None
        if PRESIDIO_AVAILABLE:
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
            except Exception as e:
                logger.warning("Presidio initialization warning, using regex engine", error=str(e))

    def _get_aes_key(self) -> bytes:
        raw_key = settings.AES_GCM_SECRET_KEY
        if len(raw_key) == 64:  # Hex representation
            return bytes.fromhex(raw_key)
        elif len(raw_key) >= 32:
            return raw_key[:32].encode("utf-8")
        else:
            return raw_key.ljust(32, "0").encode("utf-8")

    def encrypt_token(self, plaintext: str) -> str:
        """
        Encrypt original PII token using AES-256-GCM.
        Returns Base64 encoded string of (nonce + ciphertext + auth_tag).
        """
        nonce = os.urandom(12)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt_token(self, encrypted_b64: str) -> str:
        """
        Decrypt Base64 encoded AES-256-GCM token back to plaintext.
        """
        try:
            data = base64.b64decode(encrypted_b64.encode("utf-8"))
            nonce = data[:12]
            ciphertext = data[12:]
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except Exception as e:
            logger.error("Failed to decrypt PII token", error=str(e))
            raise ValueError("Invalid encrypted PII payload or unauthorized key.")

    def redact_text(self, text: str, field_path: str = "input_text") -> Tuple[str, List[Dict[str, Any]]]:
        """
        Scans text for PII entities, replaces them with `<REDACTED_ENTITY>`, and
        returns both the redacted text and a list of redaction metadata dicts with encrypted original tokens.
        """
        if not text:
            return text, []

        redactions: List[Dict[str, Any]] = []
        redacted_text = text

        # Use Regex patterns for deterministic financial/identity compliance
        for entity_type, pattern in REGEX_PATTERNS.items():
            for match in re.finditer(pattern, redacted_text):
                original_token = match.group(0)
                # Avoid trivial short false positives for account numbers
                if entity_type == "BANK_ACCOUNT" and len(original_token) < 10:
                    continue
                start_idx = match.start()
                end_idx = match.end()
                encrypted_token = self.encrypt_token(original_token)
                replacement = f"<REDACTED_{entity_type}>"

                redacted_text = redacted_text.replace(original_token, replacement)
                PII_REDACTION_COUNTER.labels(entity_type=entity_type).inc()

                redactions.append({
                    "entity_type": entity_type,
                    "original_encrypted": encrypted_token,
                    "redacted_text": replacement,
                    "start_index": start_idx,
                    "end_index": end_idx,
                    "field_path": field_path,
                })

        return redacted_text, redactions


pii_redactor = PIIRedactor()
