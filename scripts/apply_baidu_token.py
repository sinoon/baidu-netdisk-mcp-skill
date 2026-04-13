#!/usr/bin/env python3
"""Extract a Baidu Netdisk access token and patch Codex MCP config."""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DEFAULT_CONFIG = Path("~/.codex/config.toml").expanduser()
DEFAULT_SSE_BASE = "https://mcp-pan.baidu.com/sse?access_token="


def extract_token(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        raise ValueError("empty input")

    if "access_token=" in raw or raw.startswith(("http://", "https://")):
        parsed = urlparse(raw)
        for source in (parsed.fragment, parsed.query):
            values = parse_qs(source).get("access_token")
            if values and values[0]:
                return values[0]
        raise ValueError("no access_token found in URL")

    if re.fullmatch(r"[A-Za-z0-9._-]+", raw):
        return raw

    raise ValueError("input is neither a token nor a URL containing access_token")


def table_pattern(server_name: str, suffix: str = "") -> str:
    quoted = re.escape(server_name)
    return f'(?:{quoted}|"{quoted}")'


def replace_sse_url(content: str, server_name: str, token: str, sse_base: str) -> str:
    server = table_pattern(server_name)
    pattern = re.compile(
        rf'(\[mcp_servers\.{server}\][\s\S]*?url\s*=\s*")[^"]+(")',
        re.S,
    )
    updated, count = pattern.subn(rf"\1{sse_base}{token}\2", content, count=1)
    if count != 1:
        raise ValueError(f"could not update url in [mcp_servers.{server_name}]")
    return updated


def replace_upload_token(
    content: str,
    server_name: str,
    env_key: str,
    token: str,
) -> str:
    server = table_pattern(server_name)
    pattern = re.compile(
        rf'(\[mcp_servers\.{server}\.env\][\s\S]*?{re.escape(env_key)}\s*=\s*")[^"]+(")',
        re.S,
    )
    updated, count = pattern.subn(rf"\1{token}\2", content, count=1)
    if count != 1:
        raise ValueError(
            f"could not update {env_key} in [mcp_servers.{server_name}.env]"
        )
    return updated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Patch Baidu Netdisk tokens in a Codex MCP config."
    )
    parser.add_argument("token_or_url", help="Raw token or OAuth redirect URL")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Codex config path (default: ~/.codex/config.toml)",
    )
    parser.add_argument(
        "--sse-server",
        default="baidu-netdisk",
        help="Remote MCP server name (default: baidu-netdisk)",
    )
    parser.add_argument(
        "--upload-server",
        default="baidu-netdisk-upload",
        help="Uploader MCP server name (default: baidu-netdisk-upload)",
    )
    parser.add_argument(
        "--env-key",
        default="BAIDU_NETDISK_ACCESS_TOKEN",
        help="Uploader env var name (default: BAIDU_NETDISK_ACCESS_TOKEN)",
    )
    parser.add_argument(
        "--sse-base",
        default=DEFAULT_SSE_BASE,
        help=f'SSE URL prefix (default: "{DEFAULT_SSE_BASE}")',
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip writing a timestamped backup",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = extract_token(args.token_or_url)
    config_path = args.config.expanduser()

    if not config_path.exists():
        raise FileNotFoundError(f"config not found: {config_path}")

    original = config_path.read_text(encoding="utf-8")
    updated = replace_sse_url(original, args.sse_server, token, args.sse_base)
    updated = replace_upload_token(updated, args.upload_server, args.env_key, token)

    if updated == original:
        print("No config changes were needed.")
        return 0

    if not args.no_backup:
        backup_path = config_path.with_name(
            f"{config_path.name}.bak-baidu-token-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )
        shutil.copy2(config_path, backup_path)
        print(f"Backup saved to {backup_path}")

    config_path.write_text(updated, encoding="utf-8")
    print(f"Updated {config_path}")
    print(f"Token prefix: {token[:8]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
