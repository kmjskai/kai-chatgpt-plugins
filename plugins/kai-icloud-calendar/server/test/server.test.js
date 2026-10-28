import test from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import path from "node:path";

function exchange(messages) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [path.resolve("bin/kai-apple-calendar-mcp.js")]);
    let stdout = "";
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", chunk => { stdout += chunk; });
    child.on("error", reject);
    child.stdin.end(messages.map(message => JSON.stringify(message)).join("\n") + "\n");
    child.on("close", () => resolve(stdout.trim().split("\n").filter(Boolean).map(line => JSON.parse(line))));
  });
}

test("initialize and tools/list expose only the v0.1 tools", async () => {
  const replies = await exchange([
    { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-06-18" } },
    { jsonrpc: "2.0", method: "notifications/initialized" },
    { jsonrpc: "2.0", id: 2, method: "tools/list", params: {} }
  ]);
  assert.equal(replies.length, 2);
  assert.equal(replies[0].result.serverInfo.name, "kai-apple-calendar");
  assert.deepEqual(replies[1].result.tools.map(tool => tool.name), ["list_calendars", "list_events", "create_event"]);
  assert.equal(replies[1].result.tools[2].annotations.idempotentHint, false);
});

test("invalid JSON receives an MCP parse error", async () => {
  const child = spawn(process.execPath, [path.resolve("bin/kai-apple-calendar-mcp.js")]);
  let stdout = "";
  child.stdout.setEncoding("utf8");
  child.stdout.on("data", chunk => { stdout += chunk; });
  child.stdin.end("not-json\n");
  await new Promise(resolve => child.on("close", resolve));
  const reply = JSON.parse(stdout.trim());
  assert.equal(reply.error.code, -32700);
});
