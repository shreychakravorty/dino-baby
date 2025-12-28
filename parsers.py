import datetime

CURRENT_LOG_DATE = None


def parse_date(text):
    text = text.lower().strip()
    today = datetime.date.today()

    if text == "today":
        return today
    if text == "yesterday":
        return today - datetime.timedelta(days=1)

    try:
        d, m = text.split()
        months = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        return datetime.date(today.year, months[m[:3]], int(d))
    except:
        return None


def parse_time(token):
    global CURRENT_LOG_DATE

    token = token.lower().strip()
    date = CURRENT_LOG_DATE or datetime.date.today()

    pm = token.endswith("p")
    am = token.endswith("a")
    if pm or am:
        token = token[:-1]

    if ":" in token:
        h, m = map(int, token.split(":"))
    else:
        h, m = int(token), 0

    if pm and h < 12:
        h += 12
    if am and h == 12:
        h = 0

    return datetime.datetime.combine(date, datetime.time(h, m))


def is_time_like(token):
    try:
        parse_time(token)
        return True
    except:
        return False


def parse_code(text):
    parts = text.split()
    if len(parts) < 2:
        return None

    code = parts[0].upper()
    rest = parts[1:]

    if code in ("F", "FEED"):
        return "feed", rest
    if code in ("S", "SLEEP"):
        return "sleep", rest
    if code in ("W", "WAKE"):
        return "wake", rest
    if code in ("D", "DIAPER"):
        return "diaper", rest
    if code in ("DP", "DIAPERPOOP", "DIAPER_POOP"):
        return "diaper_poop", rest
    if code in ("B", "BATH"):
        return "bath", rest

    # Context-sensitive M
    if code in ("M", "MASSAGE", "MOOD"):
        if rest and is_time_like(rest[0]):
            return "massage", rest
        return "mood", rest

    return None
