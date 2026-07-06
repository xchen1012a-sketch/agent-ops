"""Feishu event webhook security boundary: signature verification and AES decrypt.

飞书事件订阅的信任边界。三件事：校验请求签名、校验 verification token、解密加密事件体。
全部为纯函数，不发起任何网络调用，可脱离真实飞书离线测试。协议细节见飞书开放平台
「事件订阅 - 请求安全校验」与「事件订阅 - 数据加密」文档。
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from data_query_agent.core.errors import ForbiddenError, InputBlockedError

_AES_BLOCK_SIZE = 16


def verify_event_signature(
    *,
    timestamp: str,
    nonce: str,
    encrypt_key: str,
    body: bytes,
    signature: str,
) -> None:
    """Verify the ``X-Lark-Signature`` header of an encrypted Feishu event push.

    飞书用 ``sha256(timestamp + nonce + encrypt_key + raw_body)`` 生成签名。使用常量时间
    比较；不匹配抛 ``ForbiddenError``，绝不放行未验证请求。``body`` 必须是原始请求字节，
    不能是重新序列化后的 JSON（重排会导致签名不一致）。
    """
    raw = timestamp.encode("utf-8") + nonce.encode("utf-8") + encrypt_key.encode("utf-8") + body
    computed = hashlib.sha256(raw).hexdigest()
    if not hmac.compare_digest(computed, signature):
        raise ForbiddenError("invalid Feishu event signature")


def verify_verification_token(*, event_token: str, expected: str) -> None:
    """Verify the ``token`` field carried inside a Feishu event body.

    明文订阅模式下用于校验来源；加密模式下 token 位于解密后的 body。常量时间比较，
    不匹配抛 ``ForbiddenError``。
    """
    if not hmac.compare_digest(event_token, expected):
        raise ForbiddenError("invalid Feishu verification token")


def decrypt_event(*, encrypt: str, encrypt_key: str) -> dict[str, Any]:
    """Decrypt a Feishu ``encrypt`` payload into its JSON event object.

    算法：key = ``sha256(encrypt_key)``；密文 base64 解码后前 16 字节为 IV，其余为
    AES-256-CBC 密文，去 PKCS7 填充得 UTF-8 JSON。任何格式/填充异常一律抛
    ``InputBlockedError``，不向调用方泄露内部细节。
    """
    key = hashlib.sha256(encrypt_key.encode("utf-8")).digest()
    try:
        data = base64.b64decode(encrypt, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise InputBlockedError("Feishu encrypt payload is not valid base64") from exc
    if len(data) <= _AES_BLOCK_SIZE:
        raise InputBlockedError("Feishu encrypt payload is too short")
    iv, ciphertext = data[:_AES_BLOCK_SIZE], data[_AES_BLOCK_SIZE:]
    if len(ciphertext) % _AES_BLOCK_SIZE != 0:
        raise InputBlockedError("Feishu encrypt payload is not block-aligned")
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    plaintext = _strip_pkcs7(padded)
    try:
        parsed = json.loads(plaintext.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputBlockedError("Feishu decrypted payload is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise InputBlockedError("Feishu decrypted payload must be a JSON object")
    return parsed


def _strip_pkcs7(data: bytes) -> bytes:
    """Remove PKCS7 padding, rejecting malformed padding lengths."""
    if not data:
        raise InputBlockedError("Feishu decrypted payload is empty")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > _AES_BLOCK_SIZE or pad_len > len(data):
        raise InputBlockedError("Feishu decrypted payload has invalid padding")
    return data[:-pad_len]
