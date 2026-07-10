---
name: browser-harness-install
description: Install browser-harness and attach to an existing authorized endpoint without browser permission UI.
---

# browser-harness install

## Invariant

Attach only. Never open or focus Chrome, open browser settings, request remote-debugging permission, or tell the user to click Allow. Authorization already exists. Every local agent reuses one shared daemon.

## Install

Use durable checkout and editable install:

```bash
cd ~/Downloads/atlas/claude-md-push/tools/browser-harness
uv sync
uv tool install --force -e .
command -v browser-harness
```

Canonical skill lives at `~/.claude/skills/browser-harness`. Other agent skill directories must symlink to canonical skills through the ClaudeMD sync script.

## Attach

Chrome Beta is preferred. Harness reads existing `DevToolsActivePort` files, skips stale ports, and connects to first live endpoint.

```bash
browser-harness --setup
browser-harness --doctor
browser-harness <<'PY'
print(page_info())
PY
```

Healthy daemon means stop. Do not run setup, reload, update, or restart during routine work. Local agents use same default daemon.

## Failure routing

- `attach-only: no DevToolsActivePort`: authorized Chrome Beta is not exposing endpoint. Return diagnostic. Do not alter browser.
- `attach-only: ... no listed endpoint is live`: wait briefly, retry once, then return diagnostic.
- `CDP WS handshake failed in attach-only mode`: preserve browser and daemon state. Use explicit `BU_CDP_WS` for dedicated or remote endpoint.
- Parallel isolated tasks: use Browser Use cloud with distinct `BU_NAME`, or dedicated CDP endpoint. Do not create multiple local Chrome attaches.

## Updates

`browser-harness --update -y` updates files but leaves live daemon running. New daemon code loads after natural restart. Never force restart solely to load update.

## Verification

```bash
python -m unittest discover -s tests -v
browser-harness --doctor
```
