<img src="assets/icon.svg" width="128" alt="Kai iCloud Calendar">

# Kai iCloud Calendar

Review calendars synchronized to your Mac and create events from confirmed arrangements.

[简体中文](README.md)

## Features

- List calendars and identify which ones are writable.
- Find events by date range, calendar, or title, including existing repeating occurrences.
- Create one confirmed non-recurring event and read it back to verify the result.

## Get started

Requires macOS 14+, Apple Silicon, Node.js 20+, and a client supporting local MCP. Configure accounts in macOS Calendar, install the plugin, and start a new local conversation.

Ask “What is on my calendar tomorrow?” or “Find this weekend's classes.” To create an event, confirm the calendar, title, start and end with timezone, all-day status, and any location, notes, and reminder.

First use may request full Calendar access for **Kai Apple Calendar Helper**. macOS does not provide a separate read-only permission for this workflow; operations remain limited by the tools and your explicit request.

## Data and privacy

The plugin reads the local calendar store through EventKit. macOS handles synchronization. You do not provide an Apple password. Query results go to your AI client under its data policies. The plugin does not separately log calendar content.

It can access multiple accounts available on the system. It does not provide an independent cloud connection or switch iCloud regions. It is not affiliated with Apple or OpenAI's official iCloud plugin.

## Limitations and recovery

Updating, deleting, and creating repeating events are not supported. If creation has an unclear outcome, search existing events before retrying.

For missing data, check macOS Calendar synchronization. For permission errors, check the helper in System Settings → Privacy & Security → Calendars. Mobile and browser-only conversations cannot run this helper directly.

Uninstall with `codex plugin remove kai-icloud-calendar@kai-chatgpt-plugins`. Uninstalling does not delete events or revoke system access automatically.

Build source is in `server/`. Run `npm run build` and `npm test` there. Rebuilt helpers use local ad-hoc signing; Developer ID signing and notarization for distribution are separate steps.

## License

The plugin and bundled calendar Skill use the [Apache License 2.0](LICENSE). Attribution is in [NOTICE](NOTICE). Include versions and errors in feedback, without passwords or private schedules.
