"""Unit tests for the Feishu event security boundary (FEISHU-100)."""

from __future__ import annotations

import base64
import hashlib
import json

import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from data_query_agent.core.errors import ForbiddenError, InputBlockedError
from data_query_agent.infrastructure.integrations.feishu_signature import (
    decrypt_event,
    verify_event_signature,
    verify_verification_token,
)

_ENCRYPT_KEY = "test-encrypt-key"
_BLOCK = 16


def _encrypt(plaintext: str, encrypt_key: str) -> str:
    """Produce a Feishu-compatible encrypt payload for round-trip testing."""
    key = hashlib.sha256(encrypt_key.encode("utf-8")).digest()
    iv = b"\x11" * _BLOCK
    raw = plaintext.encode("utf-8")
    pad_len = _BLOCK - (len(raw) % _BLOCK)
    padded = raw + bytes([pad_len]) * pad_len
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext).decode("ascii")


def test_decrypt_event_round_trips_json_object() -> None:
    event = {"type": "url_verification", "challenge": "abc", "token": "vt"}
    encrypt = _encrypt(json.dumps(event), _ENCRYPT_KEY)

    assert decrypt_event(encrypt=encrypt, encrypt_key=_ENCRYPT_KEY) == event


def test_decrypt_event_rejects_non_base64() -> None:
    with pytest.raises(InputBlockedError):
        decrypt_event(encrypt="not*base64*", encrypt_key=_ENCRYPT_KEY)


def test_decrypt_event_rejects_wrong_key() -> None:
    encrypt = _encrypt(json.dumps({"k": "v"}), _ENCRYPT_KEY)
    with pytest.raises(InputBlockedError):
        decrypt_event(encrypt=encrypt, encrypt_key="different-key")


def test_verify_event_signature_accepts_matching_signature() -> None:
    body = b'{"encrypt":"payload"}'
    timestamp, nonce = "1700000000", "nonce-1"
    expected = hashlib.sha256(
        timestamp.encode() + nonce.encode() + _ENCRYPT_KEY.encode() + body
    ).hexdigest()

    verify_event_signature(
        timestamp=timestamp,
        nonce=nonce,
        encrypt_key=_ENCRYPT_KEY,
        body=body,
        signature=expected,
    )


def test_verify_event_signature_rejects_tampered_body() -> None:
    body = b'{"encrypt":"payload"}'
    timestamp, nonce = "1700000000", "nonce-1"
    expected = hashlib.sha256(
        timestamp.encode() + nonce.encode() + _ENCRYPT_KEY.encode() + body
    ).hexdigest()

    with pytest.raises(ForbiddenError):
        verify_event_signature(
            timestamp=timestamp,
            nonce=nonce,
            encrypt_key=_ENCRYPT_KEY,
            body=b'{"encrypt":"tampered"}',
            signature=expected,
        )


def test_verify_verification_token_pass_and_reject() -> None:
    verify_verification_token(event_token="vt", expected="vt")
    with pytest.raises(ForbiddenError):
        verify_verification_token(event_token="wrong", expected="vt")
