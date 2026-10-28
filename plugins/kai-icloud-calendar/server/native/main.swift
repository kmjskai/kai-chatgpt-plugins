import EventKit
import Foundation
import Darwin

func becomeCalendarPermissionResponsibleProcess() {
    let marker = "KAI_APPLE_CALENDAR_DISCLAIMED"
    guard ProcessInfo.processInfo.environment[marker] == nil else { return }
    guard let symbol = dlsym(UnsafeMutableRawPointer(bitPattern: -2), "responsibility_spawnattrs_setdisclaim") else { return }
    typealias SetDisclaim = @convention(c) (UnsafeMutablePointer<posix_spawnattr_t?>, Int32) -> Int32
    let setDisclaim = unsafeBitCast(symbol, to: SetDisclaim.self)
    guard let executable = Bundle.main.executablePath else { return }

    var attributes: posix_spawnattr_t?
    guard posix_spawnattr_init(&attributes) == 0 else { return }
    defer { posix_spawnattr_destroy(&attributes) }
    guard posix_spawnattr_setflags(&attributes, Int16(POSIX_SPAWN_SETEXEC)) == 0 else { return }
    guard setDisclaim(&attributes, 1) == 0 else { return }

    var environment = ProcessInfo.processInfo.environment
    environment[marker] = "1"
    var arguments = CommandLine.arguments.map { strdup($0) as UnsafeMutablePointer<CChar>? }
    arguments.append(nil)
    var variables = environment.map { strdup("\($0.key)=\($0.value)") as UnsafeMutablePointer<CChar>? }
    variables.append(nil)
    defer {
        arguments.compactMap { $0 }.forEach { free($0) }
        variables.compactMap { $0 }.forEach { free($0) }
    }
    var pid: pid_t = 0
    _ = posix_spawn(&pid, executable, nil, &attributes, &arguments, &variables)
}

enum HelperError: Error, CustomStringConvertible {
    case invalid(String)
    case permission(String)
    case notFound(String)
    case save(String)

    var description: String {
        switch self {
        case .invalid(let message), .permission(let message), .notFound(let message), .save(let message): return message
        }
    }
}

let isoWithFraction = ISO8601DateFormatter()
isoWithFraction.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
isoWithFraction.timeZone = .current
let iso = ISO8601DateFormatter()
iso.formatOptions = [.withInternetDateTime]

func parseDate(_ value: Any?, field: String) throws -> Date {
    guard let text = value as? String, let date = isoWithFraction.date(from: text) ?? iso.date(from: text) else {
        throw HelperError.invalid("\(field) must be an ISO 8601 timestamp including a time-zone offset")
    }
    return date
}

func dateText(_ date: Date) -> String { isoWithFraction.string(from: date) }

func requestAccess(_ store: EKEventStore) throws {
    let status = EKEventStore.authorizationStatus(for: .event)
    if status == .fullAccess { return }
    if status == .denied || status == .restricted {
        throw HelperError.permission("Calendar full access is not available (authorization status: \(status.rawValue)). Enable it in System Settings > Privacy & Security > Calendars.")
    }

    let semaphore = DispatchSemaphore(value: 0)
    var granted = false
    var accessError: Error?
    store.requestFullAccessToEvents { ok, error in
        granted = ok
        accessError = error
        semaphore.signal()
    }
    if semaphore.wait(timeout: .now() + 60) == .timedOut {
        throw HelperError.permission("Timed out waiting for Calendar permission")
    }
    if !granted {
        throw HelperError.permission(accessError?.localizedDescription ?? "Calendar full access was not granted")
    }
}

func calendarType(_ value: EKCalendarType) -> String {
    switch value {
    case .local: return "local"
    case .calDAV: return "caldav"
    case .exchange: return "exchange"
    case .subscription: return "subscription"
    case .birthday: return "birthday"
    @unknown default: return "unknown"
    }
}

func calendarJSON(_ calendar: EKCalendar) -> [String: Any] {
    [
        "id": calendar.calendarIdentifier,
        "title": calendar.title,
        "source": calendar.source.title,
        "type": calendarType(calendar.type),
        "writable": calendar.allowsContentModifications
    ]
}

func eventJSON(_ event: EKEvent) -> [String: Any] {
    var result: [String: Any] = [
        "id": event.eventIdentifier ?? "",
        "calendar_id": event.calendar.calendarIdentifier,
        "calendar_title": event.calendar.title,
        "title": event.title ?? "",
        "start": dateText(event.startDate),
        "end": dateText(event.endDate),
        "is_all_day": event.isAllDay,
        "time_zone": TimeZone.current.identifier
    ]
    if let location = event.location, !location.isEmpty { result["location"] = location }
    if let notes = event.notes, !notes.isEmpty { result["notes"] = notes }
    if let url = event.url?.absoluteString { result["url"] = url }
    return result
}

func listCalendars(_ store: EKEventStore) -> [String: Any] {
    let calendars = store.calendars(for: .event)
        .sorted { lhs, rhs in
            let byTitle = lhs.title.localizedCaseInsensitiveCompare(rhs.title)
            return byTitle == .orderedSame ? lhs.calendarIdentifier < rhs.calendarIdentifier : byTitle == .orderedAscending
        }
        .map(calendarJSON)
    return ["calendars": calendars, "count": calendars.count]
}

func listEvents(_ payload: [String: Any], store: EKEventStore) throws -> [String: Any] {
    let start = try parseDate(payload["start"], field: "start")
    let end = try parseDate(payload["end"], field: "end")
    guard end > start else { throw HelperError.invalid("end must be later than start") }
    guard end.timeIntervalSince(start) <= 366 * 24 * 3600 else { throw HelperError.invalid("event query range cannot exceed 366 days") }

    var selected: [EKCalendar]? = nil
    if let ids = payload["calendar_ids"] as? [String], !ids.isEmpty {
        let all = store.calendars(for: .event)
        let byID = Dictionary(uniqueKeysWithValues: all.map { ($0.calendarIdentifier, $0) })
        selected = try ids.map { id in
            guard let calendar = byID[id] else { throw HelperError.notFound("Calendar not found: \(id)") }
            return calendar
        }
    }

    let predicate = store.predicateForEvents(withStart: start, end: end, calendars: selected)
    var events = store.events(matching: predicate)
    if let query = payload["query"] as? String, !query.isEmpty {
        events = events.filter { ($0.title ?? "").localizedCaseInsensitiveContains(query) }
    }
    let requestedLimit = payload["limit"] as? Int ?? 200
    let limit = max(1, min(requestedLimit, 1000))
    let truncated = events.count > limit
    let output = events.prefix(limit).map(eventJSON)
    return ["events": output, "count": output.count, "truncated": truncated, "range_start": dateText(start), "range_end": dateText(end)]
}

func createEvent(_ payload: [String: Any], store: EKEventStore) throws -> [String: Any] {
    guard let calendarID = payload["calendar_id"] as? String, !calendarID.isEmpty else { throw HelperError.invalid("calendar_id is required") }
    guard let title = payload["title"] as? String, !title.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { throw HelperError.invalid("title is required") }
    let start = try parseDate(payload["start"], field: "start")
    let end = try parseDate(payload["end"], field: "end")
    guard end > start else { throw HelperError.invalid("end must be later than start") }
    guard let calendar = store.calendar(withIdentifier: calendarID) else { throw HelperError.notFound("Calendar not found: \(calendarID)") }
    guard calendar.allowsContentModifications else { throw HelperError.invalid("Calendar is read-only: \(calendar.title)") }

    let event = EKEvent(eventStore: store)
    event.calendar = calendar
    event.title = title.trimmingCharacters(in: .whitespacesAndNewlines)
    event.startDate = start
    event.endDate = end
    event.isAllDay = payload["is_all_day"] as? Bool ?? false
    if let location = payload["location"] as? String { event.location = location }
    if let notes = payload["notes"] as? String { event.notes = notes }
    if let minutes = payload["alarm_minutes_before"] as? Int {
        guard minutes >= 0 && minutes <= 10080 else { throw HelperError.invalid("alarm_minutes_before must be between 0 and 10080") }
        event.addAlarm(EKAlarm(relativeOffset: TimeInterval(-minutes * 60)))
    }

    do { try store.save(event, span: .thisEvent, commit: true) }
    catch { throw HelperError.save("EventKit save failed: \(error.localizedDescription)") }
    guard let identifier = event.eventIdentifier, let saved = store.event(withIdentifier: identifier) else {
        throw HelperError.save("Event was saved but could not be read back; do not retry automatically")
    }
    guard saved.title == event.title && saved.startDate == start && saved.endDate == end && saved.calendar.calendarIdentifier == calendarID else {
        throw HelperError.save("Event readback did not match the requested fields; do not retry automatically")
    }
    return ["created": true, "event": eventJSON(saved)]
}

func main() {
    becomeCalendarPermissionResponsibleProcess()
    do {
        guard CommandLine.arguments.count == 2 else { throw HelperError.invalid("Expected one command argument") }
        let input = FileHandle.standardInput.readDataToEndOfFile()
        let payload = input.isEmpty ? [:] : (try JSONSerialization.jsonObject(with: input) as? [String: Any] ?? [:])
        let store = EKEventStore()
        try requestAccess(store)
        let result: [String: Any]
        switch CommandLine.arguments[1] {
        case "list-calendars": result = listCalendars(store)
        case "list-events": result = try listEvents(payload, store: store)
        case "create-event": result = try createEvent(payload, store: store)
        default: throw HelperError.invalid("Unknown command")
        }
        let data = try JSONSerialization.data(withJSONObject: ["ok": true, "result": result], options: [.sortedKeys])
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([0x0A]))
    } catch {
        let data = try! JSONSerialization.data(withJSONObject: ["ok": false, "error": String(describing: error)], options: [.sortedKeys])
        FileHandle.standardOutput.write(data)
        FileHandle.standardOutput.write(Data([0x0A]))
        exit(1)
    }
}

main()
