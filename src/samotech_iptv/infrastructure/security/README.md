# Infrastructure / Security

## Phase A Status

Empty scaffold.

## Phase B Plan

- `KeyringCredentialStore(CredentialStorePort)` — wraps `keyring.get_password` /
  `set_password` / `delete_password`.
- The MAG provider's inline keyring calls will be removed and delegated here.
