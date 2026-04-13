# Validated Behaviors

These notes capture behaviors observed during a live Baidu Netdisk MCP validation on macOS in April 2026. Treat them as high-signal operating notes, not universal guarantees for every upstream revision.

## Observed Tool Surface

- Remote server tools observed in a live session included:
  - `user_info`
  - `get_quota`
  - `file_list`
  - `file_meta`
  - `make_dir`
  - `file_del`
  - `file_copy`
  - `file_move`
  - `file_rename`
  - `file_keyword_search`
  - `file_semantics_search`
  - `file_upload_by_content`
  - `file_upload_by_url`
  - `file_doc_list`
  - `file_image_list`
  - `file_video_list`
  - `file_sharelink_set`
- The local stdio uploader exposed one tool:
  - `upload_file`

## Behaviors Worth Trusting

- `user_info` and `get_quota` were reliable first checks for token validity.
- `file_list(dir=target_dir)` was the best short-latency verifier after uploads and directory changes.
- A reversible `make_dir` plus `file_del` smoke test was a practical way to confirm write access.
- `file_meta` plus `fsid` was the safest move-audit pattern when a path looked suspicious after a reorg.

## Traps And Mismatches

- README mismatch: one validated repo snapshot used `fileupload_tool.py` as the working uploader entrypoint.
- Tool-name mismatch: the live tool list exposed `file_upload_by_content`, not `file_upload_by_text`.
- Path-encoding trap: URL-encoding the `make_dir.path` argument created a literal encoded folder name instead of the intended raw path.
- Search-lag trap: `file_keyword_search` did not reliably show a just-created folder or a fresh upload right away.
- Fuzzy-search trap: `file_keyword_search` could still return loosely related entries even when the result summary implied zero exact matches.
- Pagination trap: omitting `page` from `file_list` behaved like "page 1" rather than "all pages" during a large root inventory.
- Category trap: recursive `file_list` traversal did not always distinguish files from directories cleanly.
- Empty-list trap: probing `file_list(dir=<file-like-path>)` could return `errno=0` and `list=[]` instead of a clear type error.
- Verification trap: `file_meta.path` came back URL-encoded after successful moves and had to be decoded before comparison.
- Error-shape trap: some failures returned Chinese prose with an embedded JSON payload instead of clean JSON.
- Moveability trap: a visible directory was not always movable; some paths still returned blocking errors.
- Leaf-precreate trap: pre-creating a destination leaf before moving a directory with the same name into that parent could cause a duplicate-style failure and leave both paths in place.
- Startup trap: `uv run fileupload_tool.py` was much slower and more opaque than running the project's prepared virtualenv directly.
- Interpreter trap: helper scripts that imported `mcp` failed under the system Python when that interpreter did not have the package installed.

## Recovery Habits

- Re-check the live tool list before assuming the README is still accurate.
- Decode paths from `file_meta` before using them in assertions or audit scripts.
- For long-running uploads, use detached sessions plus resumable state files.
- When a move looks wrong, verify object identity with `fsid` before doing corrective work.
