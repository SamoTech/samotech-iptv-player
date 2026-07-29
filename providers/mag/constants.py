"""Static constants used across the MAG provider."""

# Stalker portal API endpoints (relative to portal base URL)
ENDPOINT_HANDSHAKE   = "/server/load.php"
ENDPOINT_PROFILE     = "/server/load.php?type=account_info&action=get_main_info"
ENDPOINT_CHANNELS    = "/server/load.php?type=itv&action=get_all_channels"
ENDPOINT_VOD         = "/server/load.php?type=vod&action=get_ordered_list"
ENDPOINT_SERIES      = "/server/load.php?type=series&action=get_ordered_list"
ENDPOINT_EPG         = "/server/load.php?type=epg&action=get_simple_data_table"
ENDPOINT_CREATE_LINK = "/server/load.php?type=itv&action=create_link"
ENDPOINT_VOD_LINK    = "/server/load.php?type=vod&action=create_link"

# Session / token management
DEFAULT_TOKEN_TTL_S  = 3600        # Assume 1-hour token lifetime when portal omits it
MAX_RECONNECT_TRIES  = 5
RECONNECT_BASE_DELAY = 1.0         # seconds (exponential backoff base)
RECONNECT_MAX_DELAY  = 60.0        # seconds

# HTTP
DEFAULT_TIMEOUT_S    = 30
DEFAULT_MAX_RETRIES  = 3
RETRY_BASE_DELAY     = 0.5
RETRY_MAX_DELAY      = 10.0

USER_AGENT = (
    "Mozilla/5.0 (QtEmbedded; U; Linux; C) "
    "AppleWebKit/533.3 (KHTML, like Gecko) "
    "MAG200 stbapp ver: 2 rev: 250 Safari/533.3"
)
