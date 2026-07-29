"""Provider execution context.

Every provider adapter receives exactly one ``ProviderContext`` instance
through its constructor.  This is the *only* mechanism by which
infrastructure services are made available to adapters.

No service locator.  No module-level globals.

Immutability strategy
---------------------
- All fields are set once in ``__init__`` and never reassigned.
- ``ProviderContext`` is not a dataclass to allow deferred construction
  of the ``HttpSession`` inside ``AsyncHttpClient``.
"""
from __future__ import annotations

from typing import Optional

from samotech_iptv.core.logging import get_logger
from samotech_iptv.infrastructure.configuration.configuration_provider import (
    ConfigurationProvider,
)
from samotech_iptv.infrastructure.network.http_client import AsyncHttpClient
from samotech_iptv.infrastructure.network.retry_policy import RetryPolicy
from samotech_iptv.infrastructure.network.timeouts import TimeoutConfig
from samotech_iptv.infrastructure.providers.provider_registry import ProviderRegistry
from samotech_iptv.infrastructure.security.keyring_credential_store import (
    KeyringCredentialStore,
)

__all__ = ["ProviderContext"]


class ProviderContext:
    """Immutable bundle of shared infrastructure services.

    Construction::

        ctx = ProviderContext.build()        # uses env-based defaults
        ctx = ProviderContext.build(overrides={"connect_timeout": 20.0})

    Or manual injection (tests)::

        ctx = ProviderContext(
            http_client=mock_client,
            credential_store=mock_store,
            config=ConfigurationProvider(),
            registry=ProviderRegistry(),
            retry_policy=RetryPolicy.no_retry(),
            timeout=TimeoutConfig(),
        )
    """

    def __init__(
        self,
        http_client: AsyncHttpClient,
        credential_store: KeyringCredentialStore,
        config: ConfigurationProvider,
        registry: ProviderRegistry,
        retry_policy: Optional[RetryPolicy] = None,
        timeout: Optional[TimeoutConfig] = None,
    ) -> None:
        self._http_client = http_client
        self._credential_store = credential_store
        self._config = config
        self._registry = registry
        self._retry_policy = retry_policy or RetryPolicy()
        self._timeout = timeout or TimeoutConfig()
        self._log = get_logger(__name__)

    # ------------------------------------------------------------------ accessors

    @property
    def http_client(self) -> AsyncHttpClient:
        return self._http_client

    @property
    def credential_store(self) -> KeyringCredentialStore:
        return self._credential_store

    @property
    def config(self) -> ConfigurationProvider:
        return self._config

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    @property
    def retry_policy(self) -> RetryPolicy:
        return self._retry_policy

    @property
    def timeout(self) -> TimeoutConfig:
        return self._timeout

    @property
    def logger(self):
        return self._log

    # ------------------------------------------------------------------ factory

    @classmethod
    def build(
        cls,
        overrides: Optional[dict] = None,
        registry: Optional[ProviderRegistry] = None,
    ) -> "ProviderContext":
        """Construct a fully wired ``ProviderContext`` from env / overrides.

        This is the standard factory for production use.
        """
        config = ConfigurationProvider(overrides=overrides)
        net_cfg = config.network_config()
        timeout = TimeoutConfig(
            connect=net_cfg.connect_timeout,
            read=net_cfg.read_timeout,
            total=net_cfg.connect_timeout + net_cfg.read_timeout + 5.0,
        )
        retry = RetryPolicy(
            max_attempts=net_cfg.max_retries,
        )
        http_client = AsyncHttpClient(timeout=timeout, retry_policy=retry)
        credential_store = KeyringCredentialStore()
        return cls(
            http_client=http_client,
            credential_store=credential_store,
            config=config,
            registry=registry or ProviderRegistry(),
            retry_policy=retry,
            timeout=timeout,
        )
