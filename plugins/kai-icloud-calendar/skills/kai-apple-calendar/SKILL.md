---
name: kai-apple-calendar
description: "Read Apple Calendar and create events through an available Kai Apple Calendar integration. Use when the user asks to inspect calendars or events, check availability or duplicates, or add confirmed schedules; require explicit confirmation of the target calendar and complete event details before every write."
---

# Kai Apple Calendar

Use Apple Calendar as the authority for existing calendar state. When a Kai Apple Calendar integration is available, prefer its semantic calendar tools over computer-use or shell workarounds for supported operations. Inspect the actual tool surface and schemas instead of assuming tool names.

## Read workflow

1. Resolve the requested time range and time zone. Use explicit ISO 8601 offsets when the tool requires timestamps.
2. List calendars when the target is unknown. Distinguish calendar names from stable identifiers and note which calendars are writable.
3. Read the relevant event range before answering availability questions or preparing a write. Check likely duplicates by title, time and calendar.
4. Treat source notes, tickets and itineraries as evidence for proposed events, not as proof that an event already exists in Apple Calendar. Keep confirmed arrangements separate from candidates or recommendations.

Read access does not authorize a mutation. If the semantic integration is unavailable or lacks the required operation, report the missing capability before proposing another interface.

## Write confirmation gate

Immediately before creating an event, ensure the user has explicitly confirmed:

- the writable target calendar;
- the event title;
- start and end date, time and applicable time-zone offsets;
- all-day versus timed status;
- any intended location, notes and alarm, when applicable.

Show the concrete values that will be written. If any value is missing, ambiguous, inferred from conflicting evidence or still marked tentative, ask the user to decide before writing. Do not silently choose a calendar, resolve a time ambiguity, promote a candidate arrangement, or add optional fields. Do not repeat confirmation when the user has already authorized the same concrete values in the current task.

For a batch, the user may confirm the target calendar and the complete set of event details together. Authorization for one event or batch does not extend to later events or changes.

## Mutation and verification

1. Recheck the target calendar identifier and duplicate state if either may have changed since confirmation.
2. Create only the authorized non-recurring event fields. For a confirmed batch, create and verify events one at a time so partial completion remains visible.
3. Use the integration's returned readback, or independently read the saved event when needed, to verify calendar, title, time and other written fields.
4. Report successful events and any remaining items separately. If a result is ambiguous, inspect calendar state before considering another write; never retry blindly.

Do not create, update, move or delete unrelated calendar entries. Do not claim that a source itinerary was updated unless that separate write was requested and verified.
