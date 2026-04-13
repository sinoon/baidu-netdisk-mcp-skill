---
name: baidu-netdisk-mcp
description: Use and debug the official Baidu Netdisk MCP. Trigger when Codex needs to authenticate Baidu Netdisk, refresh OAuth tokens, list or search files, manage folders, upload local files, or work around known mismatches between README examples and live MCP behavior.
---

# Baidu Netdisk MCP

## Quick Start

- Read [references/validated-behaviors.md](references/validated-behaviors.md) when the live MCP behavior differs from the README or when a bulk operation looks suspicious.
- Treat the integration as two separate servers:
  - `baidu-netdisk` for remote browse, search, metadata, quota, share, and file-management operations.
  - `baidu-netdisk-upload` for local-file uploads through a stdio tool.
- Prefer validation before mutations. Start read-only, then use a reversible smoke test, then run the real operation.

## Recommended Codex MCP Layout

Use one remote server plus one local uploader. Replace the placeholder paths with the local checkout of the official `baidu-netdisk/mcp` repository.

```toml
[mcp_servers.baidu-netdisk]
transport = "streamable_http"
url = "https://mcp-pan.baidu.com/sse?access_token=<TOKEN>"

[mcp_servers.baidu-netdisk-upload]
command = "/path/to/baidu-netdisk-mcp/src/baidu-netdisk/.venv/bin/python"
args = ["/path/to/baidu-netdisk-mcp/src/baidu-netdisk/fileupload_tool.py"]

[mcp_servers.baidu-netdisk-upload.env]
BAIDU_NETDISK_ACCESS_TOKEN = "<TOKEN>"
```

## Token Workflow

- Complete the Baidu OAuth flow in a browser.
- Extract the `access_token` from the final `login_success#...` URL fragment, or pass the raw token directly.
- Update both MCP server entries with:

```bash
python3 scripts/apply_baidu_token.py '<login_success URL or raw token>'
```

- Use `--config` if the Codex config is not at `~/.codex/config.toml`.

## Validation Order

1. Run `user_info` to confirm the token works.
2. Run `get_quota` to confirm the account is readable.
3. Run `file_list(dir=target_dir, page=1)` before touching the target.
4. If write access matters, create and remove a temporary folder first.
5. For uploads, use the stdio uploader and verify the result with `file_list`, not only keyword search.
6. For moves or audits, confirm the object with `file_meta` and compare `fsid` when available.

## Stable Operating Pattern

- Use the remote MCP server for `user_info`, `get_quota`, `file_list`, `file_meta`, `make_dir`, `file_copy`, `file_move`, `file_rename`, `file_del`, search, and share-link work.
- Use the stdio uploader only for local-file uploads.
- When a long upload or reorg must survive disconnects, keep it in a detached `tmux` session and write resumable state to disk.
- If README examples and live behavior disagree, trust the live tool list and direct API results.

## Known Pitfalls

- Verify the uploader entrypoint in the checked-out repo. Some snapshots exposed `fileupload_tool.py` even when README examples mentioned a different filename.
- The live content-upload tool can be `file_upload_by_content` even when docs mention `file_upload_by_text`.
- `make_dir.path` may need the raw absolute path instead of a URL-encoded string.
- `file_keyword_search` can lag after creates or uploads, and it can also return fuzzy matches. Do not use it as the only verification step.
- `file_list` may behave like a paginated API even when the docs imply otherwise. Pass `page` explicitly when inventory matters.
- `file_meta.path` may come back URL-encoded after a move. Decode it before comparing paths.
- Local helper scripts that import `mcp` should usually run with the project's virtualenv interpreter, not the system Python.
- Plain shell background jobs are brittle for long uploads. Detached `tmux` sessions are safer.
