from __future__ import annotations

import pytest

from samotech_iptv.core.error_taxonomy import safe_user_message
from samotech_iptv.core.exceptions import (
    AuthenticationError,
    AuthorisationError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    ProviderError,
    StorageError,
    TimeoutError,
    ValidationError,
)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (AuthenticationError("password=secret"), "Authentication failed"),
        (AuthorisationError("token=secret"), "The provider denied this action"),
        (
            ConfigurationError("https://user:secret@example.test"),
            "The provider configuration is invalid",
        ),
        (NetworkError("https://stream.example.test/live"), "The provider network is unavailable"),
        (TimeoutError("provider timed out"), "The provider request timed out"),
        (ProviderError("raw provider payload"), "The provider returned an error"),
        (StorageError("database path"), "Local storage is unavailable"),
        (NotFoundError("movie", "private-id"), "The requested item was not found"),
        (ValidationError("field", "invalid"), "The supplied input is invalid"),
        (RuntimeError("private implementation detail"), "Fallback message"),
    ],
)
def test_safe_user_message_is_stable_and_secret_free(error: BaseException, expected: str) -> None:
    message = safe_user_message(error, fallback="Fallback message")

    assert message == expected
    assert "secret" not in message
    assert "https://" not in message
    assert "private" not in message
