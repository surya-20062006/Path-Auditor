import pytest
from audit.redactor import pii_redactor


def test_pii_redaction_and_encryption():
    sample_text = "Applicant PAN is ABCDE1234F and email is john.doe@enterprise.com requesting $150,000."
    redacted_text, redactions = pii_redactor.redact_text(sample_text)

    assert "ABCDE1234F" not in redacted_text
    assert "john.doe@enterprise.com" not in redacted_text
    assert "<REDACTED_" in redacted_text
    assert len(redactions) >= 2

    # Test token decryption
    first_redaction = redactions[0]
    token = first_redaction["original_encrypted"]
    decrypted = pii_redactor.decrypt_token(token)
    assert decrypted in ["ABCDE1234F", "john.doe@enterprise.com"]


def test_invalid_token_decryption():
    with pytest.raises(Exception):
        pii_redactor.decrypt_token("invalid_token_string")
