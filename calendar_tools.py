"""Google Calendar helpers (primary calendar, Asia/Jerusalem). No deletes."""
from datetime import date as date_cls, datetime, time, timedelta
from zoneinfo import ZoneInfo

from google_auth import calendar_service

TZ_NAME = "Asia/Jerusalem"
TZ = ZoneInfo(TZ_NAME)
DAY_START = time(8, 0)   # working window used by find_free_slots
DAY_END = time(20, 0)


def _parse_dt(value: str) -> datetime:
    """Parse ISO 8601; naive values are treated as Asia/Jerusalem."""
    dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    return dt.replace(tzinfo=TZ) if dt.tzinfo is None else dt.astimezone(TZ)


def _fmt_event(ev: dict) -> dict:
    start, end = ev.get("start", {}), ev.get("end", {})
    return {
        "id": ev.get("id"),
        "title": ev.get("summary", "(no title)"),
        "start": start.get("dateTime") or start.get("date"),
        "end": end.get("dateTime") or end.get("date"),
        "all_day": "date" in start,
        "location": ev.get("location", ""),
        "link": ev.get("htmlLink"),
    }


def list_events(days_ahead: int = 7) -> list[dict]:
    days_ahead = max(1, min(int(days_ahead), 90))
    now = datetime.now(TZ)
    resp = calendar_service().events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=(now + timedelta(days=days_ahead)).isoformat(),
        singleEvents=True,
        orderBy="startTime",
        timeZone=TZ_NAME,
        maxResults=250,
    ).execute()
    return [_fmt_event(ev) for ev in resp.get("items", [])]


def find_free_slots(date: str, duration_minutes: int = 30) -> dict:
    duration_minutes = int(duration_minutes)
    if not 5 <= duration_minutes <= 720:
        raise ValueError("duration_minutes must be between 5 and 720.")
    day = date_cls.fromisoformat(date.strip())
    window_start = datetime.combine(day, DAY_START, TZ)
    window_end = datetime.combine(day, DAY_END, TZ)
    now = datetime.now(TZ)
    if window_end <= now:
        return {"date": day.isoformat(), "time_zone": TZ_NAME, "free_slots": [],
                "note": "The working window for this date is already in the past."}
    window_start = max(window_start, now.replace(second=0, microsecond=0))

    resp = calendar_service().freebusy().query(body={
        "timeMin": window_start.isoformat(),
        "timeMax": window_end.isoformat(),
        "timeZone": TZ_NAME,
        "items": [{"id": "primary"}],
    }).execute()
    busy = sorted(
        (_parse_dt(b["start"]), _parse_dt(b["end"]))
        for b in resp["calendars"]["primary"].get("busy", [])
    )

    need = timedelta(minutes=duration_minutes)
    slots, cursor = [], window_start
    for b_start, b_end in busy:
        if b_start - cursor >= need:
            slots.append((cursor, b_start))
        cursor = max(cursor, b_end)
    if window_end - cursor >= need:
        slots.append((cursor, window_end))

    return {
        "date": day.isoformat(),
        "time_zone": TZ_NAME,
        "working_window": f"{DAY_START:%H:%M}-{DAY_END:%H:%M}",
        "duration_minutes": duration_minutes,
        "free_slots": [{"start": s.isoformat(), "end": e.isoformat()} for s, e in slots],
    }


def create_event(title: str, start: str, end: str, description: str = "") -> dict:
    start_dt, end_dt = _parse_dt(start), _parse_dt(end)
    if end_dt <= start_dt:
        raise ValueError("end must be after start.")
    ev = calendar_service().events().insert(calendarId="primary", body={
        "summary": title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TZ_NAME},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TZ_NAME},
    }, sendUpdates="none").execute()
    return _fmt_event(ev)
