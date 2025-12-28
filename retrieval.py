import datetime
from storage import read_csv
from config import EVENTS_FILE, NOTES_FILE

# PRIVATE module state
_LAST_SHOWN = []


def set_last_shown(items):
    global _LAST_SHOWN
    _LAST_SHOWN = items


def get_last_shown():
    return _LAST_SHOWN


def get_last_two_days():
    cutoff = datetime.datetime.now() - datetime.timedelta(days=2)
    combined = []

    # EVENTS
    for row in read_csv(EVENTS_FILE):
        try:
            ts = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M")
        except:
            continue

        if ts < cutoff:
            continue

        event = row[2]
        display = event.upper()

        if event == "feed" and len(row) > 3 and row[3].isdigit():
            display = f"FEED ({row[3]}ml)"
        elif event == "diaper" and len(row) > 3 and row[3] == "PooPoo":
            display = "DIAPER (PooPoo)"

        combined.append((
            ts,
            f"{ts.strftime('%I:%M %p')} — {display}",
            "event",
            tuple(row)
        ))

    # NOTES
    for row in read_csv(NOTES_FILE):
        try:
            ts = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M")
        except:
            continue

        if ts < cutoff:
            continue

        combined.append((
            ts,
            f"{ts.strftime('%I:%M %p')} — 📝 {row[2]}",
            "note",
            tuple(row)
        ))

    combined.sort(key=lambda x: x[0])
    set_last_shown(combined)
    return combined
