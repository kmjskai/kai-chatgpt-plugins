#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
export CLANG_MODULE_CACHE_PATH="$(pwd)/.build/module-cache"
export SWIFT_MODULECACHE_PATH="$(pwd)/.build/module-cache"
swiftc native/main.swift \
  -target "$(uname -m)-apple-macos14.0" \
  -O \
  -framework EventKit \
  -o .build/calendar-helper
app_dir="native/Kai Apple Calendar Helper.app"
mkdir -p "$app_dir/Contents/MacOS"
cp native/Info.plist "$app_dir/Contents/Info.plist"
cp .build/calendar-helper "$app_dir/Contents/MacOS/calendar-helper"
chmod 755 "$app_dir/Contents/MacOS/calendar-helper" bin/kai-apple-calendar-mcp.js scripts/install-codex.sh
codesign --force --deep --sign - --entitlements native/Entitlements.plist --identifier com.yingkaisun.kaiapplecalendar.helper "$app_dir"
codesign --verify --deep --strict --verbose=2 "$app_dir"
