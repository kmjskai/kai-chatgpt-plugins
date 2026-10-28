# Build from source

Requires macOS, Node.js 20+, Python 3.11+, and Xcode Command Line Tools. Normal use requires Node.js and the bundled helper, not Python or Swift.

The package includes its MCP and Swift helper source. From the repository root:

```sh
cd plugins/kai-icloud-calendar/server
npm run build
npm test
```

The build targets macOS 14 on the build machine's architecture and applies an ad-hoc signature. It does not install a standalone MCP or modify calendar permissions. Rebuilding changes the signature and may require macOS authorization again. The provided binary is arm64; Intel builds require separate validation.

After rebuilding, update the file inventory and validate the package:

```sh
cd ../../..
python3 scripts/refresh_provenance.py
python3 scripts/validate_plugin.py
```

The source revision remains recorded, but the rebuilt binary is not claimed to match the original artifact byte-for-byte. Developer ID signing, notarization and target-OS tests are separate distribution checks.
