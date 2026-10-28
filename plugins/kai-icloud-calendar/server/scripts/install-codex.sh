#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
npm run build
codex mcp remove kai_apple_calendar >/dev/null 2>&1 || true
codex mcp add kai_apple_calendar -- "$(pwd)/bin/kai-apple-calendar-mcp.js"
codex mcp get kai_apple_calendar
