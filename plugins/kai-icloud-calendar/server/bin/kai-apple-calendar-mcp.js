#!/usr/bin/env node
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const helper = path.join(root, "native", "Kai Apple Calendar Helper.app", "Contents", "MacOS", "calendar-helper");

const toolDefinitions = [
  {
    name: "list_calendars",
    description: "List Apple Calendar calendars available through the local macOS EventKit store, including stable identifiers and whether each calendar is writable.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false }
  },
  {
    name: "list_events",
    description: "List Apple Calendar event occurrences overlapping an explicit ISO 8601 time range. EventKit expands recurring events in the requested range.",
    inputSchema: {
      type: "object",
      properties: {
        start: { type: "string", description: "Inclusive ISO 8601 timestamp with time-zone offset." },
        end: { type: "string", description: "Exclusive ISO 8601 timestamp with time-zone offset." },
        calendar_ids: { type: "array", items: { type: "string" }, description: "Optional calendar identifiers returned by list_calendars." },
        query: { type: "string", description: "Optional case-insensitive title filter." },
        limit: { type: "integer", minimum: 1, maximum: 1000, default: 200 }
      },
      required: ["start", "end"],
      additionalProperties: false
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false }
  },
  {
    name: "create_event",
    description: "Create exactly one non-recurring Apple Calendar event after the user has explicitly authorized its calendar, title and time. Reads the saved event back before returning success. Do not retry automatically after an error with an ambiguous outcome.",
    inputSchema: {
      type: "object",
      properties: {
        calendar_id: { type: "string", description: "Writable target calendar identifier from list_calendars." },
        title: { type: "string" },
        start: { type: "string", description: "ISO 8601 timestamp with time-zone offset." },
        end: { type: "string", description: "ISO 8601 timestamp with time-zone offset." },
        is_all_day: { type: "boolean", default: false },
        location: { type: "string" },
        notes: { type: "string" },
        alarm_minutes_before: { type: "integer", minimum: 0, maximum: 10080 }
      },
      required: ["calendar_id", "title", "start", "end"],
      additionalProperties: false
    },
    annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false }
  }
];

function runHelper(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(helper, [command], { stdio: ["pipe", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", chunk => { stdout += chunk; });
    child.stderr.on("data", chunk => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", code => {
      try {
        const parsed = JSON.parse(stdout.trim());
        if (code !== 0 || !parsed.ok) reject(new Error(parsed.error || stderr || `helper exited ${code}`));
        else resolve(parsed.result);
      } catch (error) {
        reject(new Error(`Calendar helper failed: ${error.message}${stderr ? `; ${stderr.trim()}` : ""}`));
      }
    });
    child.stdin.end(JSON.stringify(args ?? {}));
  });
}

function validateObject(value) {
  if (value === undefined) return {};
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error("arguments must be an object");
  return value;
}

async function callTool(name, rawArgs) {
  const args = validateObject(rawArgs);
  if (name === "list_calendars") return runHelper("list-calendars", args);
  if (name === "list_events") return runHelper("list-events", args);
  if (name === "create_event") return runHelper("create-event", args);
  throw new Error(`Unknown tool: ${name}`);
}

function send(message) { process.stdout.write(`${JSON.stringify(message)}\n`); }
function success(id, result) { send({ jsonrpc: "2.0", id, result }); }
function failure(id, code, message) { send({ jsonrpc: "2.0", id: id ?? null, error: { code, message } }); }

async function handle(message) {
  if (!message || message.jsonrpc !== "2.0" || typeof message.method !== "string") {
    failure(message?.id, -32600, "Invalid Request");
    return;
  }
  const hasID = Object.prototype.hasOwnProperty.call(message, "id");
  if (!hasID) return;
  try {
    switch (message.method) {
    case "initialize":
      success(message.id, {
        protocolVersion: message.params?.protocolVersion ?? "2025-06-18",
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: "kai-apple-calendar", version: "0.1.0" },
        instructions: "Read operations are local. Call create_event only after explicit user authorization of the concrete event, then report the returned readback."
      });
      break;
    case "ping": success(message.id, {}); break;
    case "tools/list": success(message.id, { tools: toolDefinitions }); break;
    case "tools/call": {
      const result = await callTool(message.params?.name, message.params?.arguments);
      success(message.id, { content: [{ type: "text", text: JSON.stringify(result, null, 2) }], isError: false });
      break;
    }
    default: failure(message.id, -32601, "Method not found");
    }
  } catch (error) {
    if (message.method === "tools/call") {
      success(message.id, { content: [{ type: "text", text: error.message }], isError: true });
    } else failure(message.id, -32603, error.message);
  }
}

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
input.on("line", line => {
  if (!line.trim()) return;
  let message;
  try { message = JSON.parse(line); }
  catch { failure(null, -32700, "Parse error"); return; }
  void handle(message);
});
