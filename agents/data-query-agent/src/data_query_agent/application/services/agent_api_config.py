"""Fernet encryption + masked hint for the agent API config center."""

from __future__ import annotations

from cryptography.fernet import Fernet

from data_query_agent.core.errors import ConfigDecryptError, ConfigKeyTooShortError

_MIN_KEY_LENGTH = 8
_TAIL_EXPOSE = 4


class ApiConfigCrypto:
    """Encrypt/decrypt upstream API keys and build masked hints.

    The Fernet master key is provisioned via ``AGENT_CONFIG_ENCRYPTION_KEY``
    and never persists alongside the encrypted tokens.
    """

    def __init__(self, master_key: str) -> None:
        if not master_key or len(master_key) < 32:
            raise ConfigKeyTooShortError(
                "AGENT_CONFIG_ENCRYPTION_KEY must be a 32+ byte Fernet key"
            )
        self._fernet = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext key; reject values shorter than the policy floor."""

        if len(plaintext) < _MIN_KEY_LENGTH:
            raise ConfigKeyTooShortError(
                f"api_key must be at least {_MIN_KEY_LENGTH} bytes"
            )
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt(self, token: str) -> str:
        """Decrypt a stored token; map Fernet errors to ConfigDecryptError."""

        try:
            return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except Exception as exc:
            raise ConfigDecryptError("api_key decryption failed") from exc

    @staticmethod
    def hint(plaintext: str) -> str:
        """Return a masked echo such as ``sk-t****7890``; all-mask if too short."""

        if len(plaintext) < _MIN_KEY_LENGTH:
            return "****"
        prefix = plaintext[:4]
        tail = plaintext[-_TAIL_EXPOSE:]
        return f"{prefix}****{tail}"
