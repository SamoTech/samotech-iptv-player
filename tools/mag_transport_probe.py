"""Bounded MAG transport diagnostic; never prints credentials or response bodies."""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

import aiohttp
import requests


@dataclass(frozen=True)
class Target:
    scheme: str
    hostname: str
    port: int
    origin_path: str
    ip: str


TIMEOUT_S = 5.0
CONNECT_TIMEOUT_S = 3.0
QUERY = {"type": "stb", "action": "handshake", "token": "", "JsHttpRequest": "1-xml"}
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/58.0.3029.110 Safari/537.3"
)


def _target() -> Target:
    parsed = urlsplit(os.environ["MAG_PORTAL_URL"])
    if not parsed.hostname:
        raise ValueError("MAG_PORTAL_URL has no hostname")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    ipv4 = [address[4][0] for address in addresses if address[0] == socket.AF_INET]
    if not ipv4:
        raise OSError("no IPv4 address resolved")
    return Target(
        parsed.scheme or "http",
        parsed.hostname,
        port,
        parsed.path or "/c/",
        str(ipv4[0]),
    )


def _headers(mac: str, target: Target) -> dict[str, str]:
    origin = f"{target.scheme}://{target.hostname}"
    if target.port not in (80, 443):
        origin += f":{target.port}"
    return {
        "Authorization": f"MAC {mac}",
        "Cookie": f"mac={mac}",
        "User-Agent": BROWSER_UA,
        "Referer": f"{origin}/c/",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }


def _safe_exception(exc: BaseException, target: Target, mac: str) -> str:
    text = str(exc)
    for value in (target.hostname, target.ip, mac):
        if value:
            text = text.replace(value, "<redacted>")
    text = re.sub(r"https?://[^\s]+", "<redacted-url>", text)
    return text[:240]


def _base_result(name: str, target: Target) -> dict[str, object]:
    return {
        "transport": name,
        "hostname": target.hostname,
        "resolved_ip": target.ip,
        "port": target.port,
        "protocol": target.scheme,
        "connection": "failure",
        "tcp_connect": None,
        "status": None,
        "content_type": None,
        "response_size": None,
        "elapsed_seconds": None,
        "redirect_count": None,
        "server": None,
        "allow": None,
        "www_authenticate": None,
        "exception_class": None,
        "exception_message": None,
        "tls": "not_applicable",
    }


def _record_response(
    result: dict[str, object], response: object, started: float
) -> dict[str, object]:
    headers = getattr(response, "headers", {})
    body = getattr(response, "content", b"")
    result.update(
        {
            "connection": "success",
            "status": getattr(response, "status_code", getattr(response, "status", None)),
            "content_type": headers.get("Content-Type", "").split(";", 1)[0] or None,
            "response_size": len(body),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "redirect_count": len(getattr(response, "history", ()) or ()),
            "server": headers.get("Server"),
            "allow": headers.get("Allow"),
            "www_authenticate": "WWW-Authenticate" in headers,
        }
    )
    return result


def _requests_probe(target: Target, mac: str, *, use_ip: bool) -> dict[str, object]:
    name = "requests_ip_host" if use_ip else "requests_hostname"
    result = _base_result(name, target)
    url_host = target.ip if use_ip else target.hostname
    url = f"{target.scheme}://{url_host}:{target.port}/portal.php"
    headers = _headers(mac, target)
    if use_ip:
        headers["Host"] = (
            target.hostname if target.port in (80, 443) else f"{target.hostname}:{target.port}"
        )
    started = time.perf_counter()
    try:
        response = requests.get(
            url,
            params=QUERY,
            headers=headers,
            timeout=(CONNECT_TIMEOUT_S, TIMEOUT_S),
            allow_redirects=False,
            verify=True,
        )
        return _record_response(result, response, started)
    except Exception as exc:  # noqa: BLE001
        result.update(
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "exception_class": type(exc).__name__,
                "exception_message": _safe_exception(exc, target, mac),
            }
        )
        return result


async def _aiohttp_one(target: Target, mac: str, *, use_ip: bool) -> dict[str, object]:
    name = "aiohttp_ip_host" if use_ip else "aiohttp_hostname"
    result = _base_result(name, target)
    url_host = target.ip if use_ip else target.hostname
    url = f"{target.scheme}://{url_host}:{target.port}/portal.php"
    headers = _headers(mac, target)
    if use_ip:
        headers["Host"] = (
            target.hostname if target.port in (80, 443) else f"{target.hostname}:{target.port}"
        )
    started = time.perf_counter()
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_S, connect=CONNECT_TIMEOUT_S)
    try:
        connector = aiohttp.TCPConnector(ssl=target.scheme != "http")
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(
                url,
                params=QUERY,
                headers=headers,
                allow_redirects=False,
            ) as response:
                body = await response.read()
                result.update(
                    {
                        "connection": "success",
                        "status": response.status,
                        "content_type": response.headers.get("Content-Type", "").split(";", 1)[0]
                        or None,
                        "response_size": len(body),
                        "elapsed_seconds": round(time.perf_counter() - started, 3),
                        "redirect_count": len(response.history),
                        "server": response.headers.get("Server"),
                        "allow": response.headers.get("Allow"),
                        "www_authenticate": "WWW-Authenticate" in response.headers,
                        "tls": "success" if target.scheme == "https" else "not_applicable",
                    }
                )
                return result
    except Exception as exc:  # noqa: BLE001
        result.update(
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "exception_class": type(exc).__name__,
                "exception_message": _safe_exception(exc, target, mac),
                "tls": "failure" if target.scheme == "https" else "not_applicable",
            }
        )
        return result


def _raw_tcp(target: Target, mac: str, *, use_ip: bool) -> dict[str, object]:
    name = "raw_tcp_ip_host" if use_ip else "raw_tcp_hostname"
    result = _base_result(name, target)
    connect_host = target.ip if use_ip else target.hostname
    host_header = (
        target.hostname if target.port in (80, 443) else f"{target.hostname}:{target.port}"
    )
    request_target = "/portal.php?type=stb&action=handshake&token=&JsHttpRequest=1-xml"
    request = (
        f"GET {request_target} HTTP/1.1\r\nHost: {host_header}\r\n"
        f"Authorization: MAC {mac}\r\nCookie: mac={mac}\r\n"
        f"User-Agent: {BROWSER_UA}\r\nReferer: {target.scheme}://{target.hostname}/c/\r\n"
        "Accept: application/json, text/javascript, */*; q=0.01\r\n"
        "X-Requested-With: XMLHttpRequest\r\nConnection: close\r\n\r\n"
    ).encode()
    started = time.perf_counter()
    try:
        with socket.create_connection(
            (connect_host, target.port), timeout=CONNECT_TIMEOUT_S
        ) as sock:
            result["tcp_connect"] = "success"
            sock.settimeout(TIMEOUT_S)
            sock.sendall(request)
            chunks: list[bytes] = []
            total = 0
            while total < 65536:
                chunk = sock.recv(min(8192, 65536 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
        raw = b"".join(chunks)
        header_blob, _, _body = raw.partition(b"\r\n\r\n")
        header_lines = header_blob.decode("iso-8859-1", "replace").splitlines()
        status_match = (
            re.match(r"HTTP/\d(?:\.\d)?\s+(\d+)", header_lines[0]) if header_lines else None
        )
        header_map: dict[str, str] = {}
        for line in header_lines[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                header_map[key.casefold()] = value.strip()
        result.update(
            {
                "connection": "success",
                "status": int(status_match.group(1)) if status_match else None,
                "content_type": header_map.get("content-type", "").split(";", 1)[0] or None,
                "response_size": len(raw) - (len(header_blob) + 4 if b"\r\n\r\n" in raw else 0),
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "server": header_map.get("server"),
                "allow": header_map.get("allow"),
                "www_authenticate": "www-authenticate" in header_map,
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result.update(
            {
                "connection": (
                    "tcp_connected_no_http_response"
                    if result["tcp_connect"] == "success"
                    else "failure"
                ),
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "exception_class": type(exc).__name__,
                "exception_message": _safe_exception(exc, target, mac),
            }
        )
        return result


def _curl_probe(target: Target, mac: str) -> dict[str, object]:
    result = _base_result("curl", target)
    executable = shutil.which("curl.exe") or shutil.which("curl")
    if executable is None:
        result.update(
            {"exception_class": "Unavailable", "exception_message": "curl executable not found"}
        )
        return result
    url = f"{target.scheme}://{target.hostname}:{target.port}/portal.php"
    args = [
        executable,
        "--silent",
        "--show-error",
        "--connect-timeout",
        str(int(CONNECT_TIMEOUT_S)),
        "--max-time",
        str(int(TIMEOUT_S)),
        "--noproxy",
        "*",
        "--dump-header",
        "-",
        "--output",
        "-",
        "--request",
        "GET",
        "--get",
        url,
        "--data-urlencode",
        "type=stb",
        "--data-urlencode",
        "action=handshake",
        "--data-urlencode",
        "token=",
        "--data-urlencode",
        "JsHttpRequest=1-xml",
        "--header",
        f"Authorization: MAC {mac}",
        "--header",
        f"Cookie: mac={mac}",
        "--header",
        f"User-Agent: {BROWSER_UA}",
        "--header",
        f"Referer: {target.scheme}://{target.hostname}/c/",
        "--header",
        "Accept: application/json, text/javascript, */*; q=0.01",
        "--header",
        "X-Requested-With: XMLHttpRequest",
    ]
    started = time.perf_counter()
    try:
        completed = subprocess.run(  # noqa: S603
            args, capture_output=True, timeout=TIMEOUT_S + 2, check=False
        )
        raw = completed.stdout
        header_blob, separator, body = raw.partition(b"\r\n\r\n")
        lines = header_blob.decode("iso-8859-1", "replace").splitlines()
        status_match = re.match(r"HTTP/\d(?:\.\d)?\s+(\d+)", lines[0]) if lines else None
        header_map: dict[str, str] = {}
        for line in lines[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                header_map[key.casefold()] = value.strip()
        result.update(
            {
                "connection": "success" if status_match else "failure",
                "status": int(status_match.group(1)) if status_match else None,
                "content_type": header_map.get("content-type", "").split(";", 1)[0] or None,
                "response_size": len(body) if separator else None,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "server": header_map.get("server"),
                "allow": header_map.get("allow"),
                "www_authenticate": "www-authenticate" in header_map,
                "exception_class": None if status_match else f"ExitCode{completed.returncode}",
                "exception_message": None if status_match else "curl did not return an HTTP status",
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001
        result.update(
            {
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "exception_class": type(exc).__name__,
                "exception_message": _safe_exception(exc, target, mac),
            }
        )
        return result


def _unavailable(name: str, target: Target, message: str) -> dict[str, object]:
    result = _base_result(name, target)
    result.update({"exception_class": "Unavailable", "exception_message": message})
    return result


async def main() -> None:
    target = _target()
    mac = os.environ["MAG_MAC"]
    results: list[dict[str, object]] = []
    results.extend(
        [
            _requests_probe(target, mac, use_ip=False),
            _requests_probe(target, mac, use_ip=True),
            _raw_tcp(target, mac, use_ip=False),
            _raw_tcp(target, mac, use_ip=True),
            _curl_probe(target, mac),
        ]
    )
    results.extend(
        [
            await _aiohttp_one(target, mac, use_ip=False),
            await _aiohttp_one(target, mac, use_ip=True),
        ]
    )
    powershell = shutil.which("powershell.exe") or shutil.which("pwsh")
    results.append(
        _unavailable(
            "powershell_invoke_webrequest",
            target,
            "PowerShell is unavailable in this environment",
        )
        if powershell is None
        else _unavailable(
            "powershell_invoke_webrequest",
            target,
            "PowerShell execution intentionally reserved for Windows matrix",
        )
    )
    https_target = Target("https", target.hostname, 443, target.origin_path, target.ip)
    results.append(_requests_probe(https_target, mac, use_ip=False))
    print(
        json.dumps(
            {
                "target": {
                    "hostname": target.hostname,
                    "resolved_ip": target.ip,
                    "port": target.port,
                },
                "results": results,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
