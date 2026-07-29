"""
MAG / Stalker Middleware adapter.

Only use this provider with portals you own or are explicitly
authorised to access.  Never attempt to bypass authentication or
emulate identifiers to gain unauthorised access.
"""
from .provider import MAGProvider

__all__ = ["MAGProvider"]
