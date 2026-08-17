"""Audit generated Windows artifacts without exposing matched content."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_SECRET_PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "credential_url": re.compile(rb"https?://[^\s/@:]+:[^\s/@]+@"),
    "bearer_literal": re.compile(rb"(?i)\bBearer\s+[A-Za-z0-9._-]{24,}"),
    "jwt_literal": re.compile(
        rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--package-root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.exe.is_file():
        raise SystemExit(f"artifact does not exist: {args.exe}")
    payload = args.exe.read_bytes()
    findings: list[str] = []
    for label, pattern in _SECRET_PATTERNS.items():
        if pattern.search(payload):
            findings.append(label)
    if args.package_root is not None:
        if not args.package_root.is_dir():
            raise SystemExit(f"package root does not exist: {args.package_root}")
        forbidden_suffixes = {".py", ".pyc", ".pyo"}
        for path in args.package_root.rglob("*"):
            if path.is_file() and (
                path.suffix.lower() in forbidden_suffixes or path.name == ".git"
            ):
                findings.append(f"development_file:{path.name}")
        if (args.package_root / ".git").exists():
            findings.append("git_directory")
    print(f"artifact={args.exe.name}")
    print(f"artifact_bytes={len(payload)}")
    print(f"secret_findings={len(findings)}")
    for finding in findings:
        print(f"finding={finding}")
    if findings:
        return 1
    print("artifact_audit=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
