import datetime
from storage import read_csv
from config import EVENTS_FILE


def generate_summary():
    rows = read_csv(EVENTS_FILE)
    today = datetime.date.today()
    days = [today - datetime.timedelta(days=i) for i in range(3)]

    msg = "📊 Summary (last 3 days)\n\n"

    for d in reversed(days):
        feed_ml = 0
        diapers = 0
        poop_count = 0

        for r in rows:
            try:
                ts = datetime.datetime.strptime(r[0], "%Y-%m-%d %H:%M")
            except:
                continue

            if ts.date() != d:
                continue

            # Feed: only sum numeric ml values
            if r[2] == "feed" and len(r) > 3 and r[3].isdigit():
                feed_ml += int(r[3])

            # Diapers
            elif r[2] == "diaper":
                diapers += 1
                if len(r) > 3 and r[3] == "PooPoo":
                    poop_count += 1

        msg += f"📅 {d.strftime('%d %b %Y')}\n"
        msg += f"Feed: {feed_ml} ml\n"
        msg += f"Diapers: {diapers}\n"
        msg += f"PooPoos: {poop_count}\n\n"

    return msg
