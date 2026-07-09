"""Unit tests for the production Feishu webhook processor and route."""

from __future__ import annotations

import base64
import hashlib
import json

import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastapi.testclient import TestClient

from data_query_agent.api.dependencies import get_feishu_webhook_deps
from data_query_agent.application.services.feishu_bot_service import FeishuInboundMessage
from data_query_agent.application.services.feishu_webhook_service import (
    FeishuWebhookDeps,
    FeishuWebhookProcessor,
)
from data_query_agent.core.errors import ForbiddenError
from data_query_agent.infrastructure.integrations.feishu_event_dedup import (
    InMemoryFeishuEventDedupStore,
)
from data_query_agent.main import create_app

_DISABLED_DEPS = FeishuWebhookDeps(enabled=False, processor=None, dispatch=None)

_TOKEN = "vt"
_ENCRYPT_KEY = "ek"
_BLOCK = 16


def _processor(*, encrypt_key: str = "") -> FeishuWebhookProcessor:
    return FeishuWebhookProcessor(
        encrypt_key=encrypt_key,
        verification_token=_TOKEN,
        dedup=InMemoryFeishuEventDedupStore(),
    )


def _encrypt(plaintext: str) -> tuple[str, bytes]:
    key = hashlib.sha256(_ENCRYPT_KEY.encode()).digest()
    iv = b"\x22" * _BLOCK
    raw = plaintext.encode("utf-8")
    pad = _BLOCK - (len(raw) % _BLOCK)
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ct = encryptor.update(raw + bytes([pad]) * pad) + encryptor.finalize()
    encrypt = base64.b64encode(iv + ct).decode("ascii")
    body = json.dumps({"encrypt": encrypt}).encode("utf-8")
    return encrypt, body


def _message_event() -> dict[str, object]:
    return {
        "header": {"event_id": "evt-9", "event_type": "im.message.receive_v1", "token": _TOKEN},
        "event": {
            "sender": {"sender_id": {"open_id": "ou_1"}},
            "message": {"message_type": "text", "content": json.dumps({"text": "hi"})},
        },
    }


async def test_processor_url_verification_returns_challenge() -> None:
    body = json.dumps({"type": "url_verification", "challenge": "c-1", "token": _TOKEN}).encode()
    result = await _processor().process(
        raw_body=body, timestamp=None, nonce=None, signature=None
    )
    assert result.challenge == "c-1"


async def test_processor_rejects_wrong_verification_token() -> None:
    body = json.dumps({"type": "url_verification", "challenge": "c", "token": "bad"}).encode()
    with pytest.raises(ForbiddenError):
        await _processor().process(raw_body=body, timestamp=None, nonce=None, signature=None)


async def test_processor_parses_message_and_dedupes_by_event_id() -> None:
    processor = _processor()
    body = json.dumps(_message_event()).encode()

    first = await processor.process(raw_body=body, timestamp=None, nonce=None, signature=None)
    second = await processor.process(raw_body=body, timestamp=None, nonce=None, signature=None)

    assert first.message is not None
    assert first.message.open_id == "ou_1"
    assert first.message.text == "hi"
    assert second.message is None  # 同 event_id 去重


async def test_processor_decrypts_and_verifies_signature() -> None:
    _, body = _encrypt(json.dumps(_message_event()))
    timestamp, nonce = "100", "n"
    signature = hashlib.sha256(
        timestamp.encode() + nonce.encode() + _ENCRYPT_KEY.encode() + body
    ).hexdigest()

    result = await _processor(encrypt_key=_ENCRYPT_KEY).process(
        raw_body=body, timestamp=timestamp, nonce=nonce, signature=signature
    )
    assert result.message is not None
    assert result.message.open_id == "ou_1"


async def test_processor_rejects_bad_signature_on_encrypted_event() -> None:
    _, body = _encrypt(json.dumps(_message_event()))
    with pytest.raises(ForbiddenError):
        await _processor(encrypt_key=_ENCRYPT_KEY).process(
            raw_body=body, timestamp="100", nonce="n", signature="deadbeef"
        )


def test_route_returns_404_when_feishu_disabled() -> None:
    # FEISHU-300: get_feishu_webhook_deps 现在需要 repo/crypto 构造，测试无 DB 时
    # 直接 override 返回 disabled 状态，验证路由层 404 语义不变。
    app = create_app()
    app.dependency_overrides[get_feishu_webhook_deps] = lambda: _DISABLED_DEPS
    client = TestClient(app)
    response = client.post("/v1/integrations/feishu/webhook", json={"type": "url_verification"})
    assert response.status_code == 404


def _enabled_client() -> tuple[TestClient, list[FeishuInboundMessage]]:
    app = create_app()
    dispatched: list[FeishuInboundMessage] = []

    async def _dispatch(message: FeishuInboundMessage) -> None:
        dispatched.append(message)

    deps = FeishuWebhookDeps(enabled=True, processor=_processor(), dispatch=_dispatch)
    app.dependency_overrides[get_feishu_webhook_deps] = lambda: deps
    return TestClient(app), dispatched


def test_route_echoes_challenge() -> None:
    client, _ = _enabled_client()
    response = client.post(
        "/v1/integrations/feishu/webhook",
        json={"type": "url_verification", "challenge": "c-9", "token": _TOKEN},
    )
    assert response.status_code == 200
    assert response.json() == {"challenge": "c-9"}


def test_route_acks_message_and_schedules_dispatch() -> None:
    client, dispatched = _enabled_client()
    response = client.post("/v1/integrations/feishu/webhook", json=_message_event())
    assert response.status_code == 200
    assert response.json() == {"code": 0}
    assert len(dispatched) == 1
    assert dispatched[0].open_id == "ou_1"
