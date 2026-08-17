"""Audit generated Windows artifacts without exposing matched content."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"https?://[^\s/@:]+:[^\s/@]+@"),
    re.compile(rb"(?i)\bBearer\s+[A-Za-z0-9._-]{24,}"),
    re.compile(rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--package-root", type=Path)
    return parser.parse_args()


def _count_secret_findings(payload: bytes) -> int:
    return sum(1 for pattern in _SECRET_PATTERNS if pattern.search(payload) is not None)


def _count_development_files(package_root: Path) -> int:
    forbidden_suffixes = {".py", ".pyc", ".pyo"}
    return sum(
        1
        for path in package_root.rglob("*")
        if path.is_file() and (path.suffix.lower() in forbidden_suffixes or path.name == ".git")
    ) + int((package_root / ".git").exists())


def main() -> int:
    args = _parse_args()
    if not args.exe.is_file():
        raise SystemExit("artifact does not exist")
    payload = args.exe.read_bytes()
    secret_count = _count_secret_findings(payload)
    development_count = 0
    if args.package_root is not None:
        if not args.package_root.is_dir():
            raise SystemExit("package root does not exist")
        development_count = _count_development_files(args.package_root)

    total_findings = secret_count + development_count
    print("artifact_audit=FAIL" if total_findings else "artifact_audit=PASS")
    return 1 if total_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
