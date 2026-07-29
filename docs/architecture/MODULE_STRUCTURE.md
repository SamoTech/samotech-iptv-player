# Module Structure

## Why Packages Replaced Monolithic Modules

### Phase A Structure

Phase A grouped related types into four monolithic modules:

```
domain/
    entities.py       # 11 classes, 160 lines
    value_objects.py  # 5 classes, 90 lines
    repositories.py   # 6 ABCs, 110 lines
    events.py         # 6 events, 60 lines
```

This was acceptable for bootstrapping but created problems:

1. **Every class change touched the same file** — git history was noisy.
2. **IDE navigation** required scrolling through unrelated code.
3. **Cross-module circular risk** — as classes grew, internal references
   within one file made extraction harder.
4. **Testability** — importing one entity pulled in all entities.
5. **Review surface** — a PR changing `Channel` also showed diffs for
   unrelated `History` or `EPGEntry` changes.

### Phase B.0 Structure

```
domain/
    entities/
        channel.py      # 1 class
        category.py     # 1 class
        playlist.py     # 1 class
        movie.py        # 1 class
        series.py       # 1 class
        episode.py      # 1 class
        stream.py       # 1 class
        provider.py     # 1 class
        epg_entry.py    # 1 class
        favorite.py     # 1 class
        history.py      # 1 class
    value_objects/
        provider_id.py  # 1 class
        channel_id.py   # 1 class
        stream_id.py    # 1 class
        url.py          # 1 class
        credential.py   # 1 class
    repositories/
        channel_repository.py
        playlist_repository.py
        provider_repository.py
        epg_repository.py
        history_repository.py
        favorite_repository.py
    events/
        provider_events.py   # provider auth/refresh events
        playback_events.py   # stream resolved, history recorded
        library_events.py    # channels loaded, favorite saved
```

### Backward Compatibility

Phase A imports are preserved via compatibility shims:

```python
# Phase A (still works)
from samotech_iptv.domain.entities import Channel

# Phase B.0 canonical (preferred)
from samotech_iptv.domain.entities.channel import Channel
```

The shim files (`entities.py`, `value_objects.py`, `repositories.py`,
`events.py`) delegate to the new packages and will be removed in the
first major version bump.

### One Responsibility Per Module

| Principle | Before | After |
|-----------|--------|-------|
| SRP | 1 file = N classes | 1 file = 1 class |
| ISP | 1 port = 7 methods | 7 ports = 1 concern each |
| OCP | Adding entity = touching shared file | Adding entity = new file only |
| DIP | `ProviderPort` covers all | Use-case picks minimum interface |
