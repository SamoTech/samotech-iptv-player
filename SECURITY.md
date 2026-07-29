# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| `main` (latest) | ✅ |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Email: **samo.hossam@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix (optional)

You will receive a response within 72 hours. If confirmed, a patch will be released
as a priority and you will be credited in the changelog (unless you prefer anonymity).

## Security Design

- Credentials stored via Windows Credential Manager — never in SQLite or JSON
- All stream URLs validated through `url_sanitizer.py` before passing to VLC
- Input validation via Pydantic v2 on all DTO boundaries
- No `eval()`, `exec()`, or `pickle` deserialization
- Plugin sandboxing via capability-token model
