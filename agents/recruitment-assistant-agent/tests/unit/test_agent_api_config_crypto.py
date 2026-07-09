"""Unit tests for the agent API config crypto service (CONFIG-100)."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from recruitment_assistant_agent.application.services.agent_api_config import ApiConfigCrypto
from recruitment_assistant_agent.core.errors import ConfigDecryptError, ConfigKeyTooShortError


def _master_key() -> str:
    return Fernet.generate_key().decode("ascii")


def test_encrypt_then_decrypt_roundtrip() -> None:
    crypto = ApiConfigCrypto(_master_key())
    token = crypto.encrypt("sk-test-1234567890")
    assert token != "sk-test-1234567890"
    assert crypto.decrypt(token) == "sk-test-1234567890"


def test_hint_masks_middle_keeps_prefix_and_tail() -> None:
    assert ApiConfigCrypto.hint("sk-test-1234567890") == "sk-t****7890"


def test_hint_returns_all_mask_when_too_short() -> None:
    assert ApiConfigCrypto.hint("short") == "****"
    assert ApiConfigCrypto.hint("") == "****"


def test_encrypt_rejects_short_plaintext() -> None:
    crypto = ApiConfigCrypto(_master_key())
    with pytest.raises(ConfigKeyTooShortError):
        crypto.encrypt("short")


def test_constructor_rejects_short_master_key() -> None:
    with pytest.raises(ConfigKeyTooShortError):
        ApiConfigCrypto("shortkey")


def test_decrypt_with_wrong_master_key_raises_config_decrypt_error() -> None:
    encryptor = ApiConfigCrypto(_master_key())
    token = encryptor.encrypt("sk-test-1234567890")
    decryptor = ApiConfigCrypto(_master_key())
    with pytest.raises(ConfigDecryptError):
        decryptor.decrypt(token)
