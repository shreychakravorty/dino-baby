import datetime
import retrieval

from parsers import parse_date, parse_time, parse_code, CURRENT_LOG_DATE
from storage import read_csv, write_csv, push_undo, undo_last
from summary import generate_summary
from config import EVENTS_FILE, NOTES_FILE, DEFAULT_FEED_ML


async def handle_message(update, context):
    text = update.message.text.strip()
    lower = text.lower()
    user = update.message.from_user.first_name
    parsed = parse_code(text)

    # =====================
    # UNDO
    # =====================
    if lower == "undo":
        await update.message.reply_text(
            "↩️ Undone." if undo_last() else "Nothing to undo."
        )
        return

    # =====================
    # SUMMARY
    # =====================
    if lower == "summary":
        await update.message.reply_text(generate_summary())
        return

    # =====================
    # SHOW (ONLY place that sets last_shown)
    # =====================
    if lower == "show":
        timeline = retrieval.get_last_two_days()

        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        dates = [yesterday, today]

        by_date = {d: [] for d in dates}
        for item in timeline:
            by_date[item[0].date()].append(item)

        msg = "🕒 Last 2 days\n\n"
        idx = 1

        for d in dates:
            msg += f"📅 {d.strftime('%d %b %Y')}\n"
            if not by_date[d]:
                msg += "No log\n\n"
                continue

            for item in by_date[d]:
                msg += f"{idx}. {item[1]}\n"
                idx += 1

            msg += "\n"

        await update.message.reply_text(msg)
        return

    # =====================
    # DELETE (PERMANENTLY SAFE)
    # =====================
    if lower.startswith("delete"):
        last_shown = retrieval.get_last_shown()
        if not last_shown:
            await update.message.reply_text("Run 'show' first.")
            return

        parts = lower.split()[1:]
        targets = []

        for p in parts:
            if p == "last":
                targets.append(len(last_shown))
            else:
                try:
                    targets.append(int(p))
                except:
                    pass

        targets = sorted(
            {t - 1 for t in targets if 0 <= t - 1 < len(last_shown)},
            reverse=True
        )

        for idx in targets:
            _, _, src, row = last_shown[idx]
            path = EVENTS_FILE if src == "event" else NOTES_FILE

            before = read_csv(path)
            after = [r for r in before if tuple(r) != row]

            write_csv(path, after)
            push_undo(path, before)

        await update.message.reply_text(f"🗑 Deleted {len(targets)} entries.")
        return

    # =====================
    # EDIT (FEED ML BUG FIXED)
    # =====================
    if lower.startswith("edit"):
        last_shown = retrieval.get_last_shown()
        if not last_shown:
            await update.message.reply_text("Run 'show' first.")
            return

        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            await update.message.reply_text("Usage: edit <n|last> <new value>")
            return

        try:
            target = len(last_shown) - 1 if parts[1] == "last" else int(parts[1]) - 1
        except:
            await update.message.reply_text("Invalid entry number.")
            return

        if not (0 <= target < len(last_shown)):
            await update.message.reply_text("Invalid entry number.")
            return

        _, _, src, old_row = last_shown[target]
        path = EVENTS_FILE if src == "event" else NOTES_FILE

        before = read_csv(path)
        after = []

        if src == "event":
            parsed_edit = parse_code(parts[2])
            if not parsed_edit:
                await update.message.reply_text("Invalid edit format.")
                return

            event, values = parsed_edit
            t = parse_time(values[0])

            if t > datetime.datetime.now():
                await update.message.reply_text("⏳ Cannot log future time.")
                return

            # ---- FEED: re-parse ml correctly ----
            if event == "feed":
                ml = DEFAULT_FEED_ML
                if len(values) > 1 and values[1].lower().endswith("ml"):
                    ml = int(values[1][:-2])

                new_row = [
                    t.strftime("%Y-%m-%d %H:%M"),
                    old_row[1],
                    "feed",
                    str(ml)
                ]

            # ---- OTHER EVENTS ----
            else:
                new_row = [
                    t.strftime("%Y-%m-%d %H:%M"),
                    old_row[1],
                    event
                ]
                if len(old_row) > 3:
                    new_row.append(old_row[3])

        else:
            # NOTE edit
            new_row = [old_row[0], old_row[1], parts[2]]

        for r in before:
            after.append(new_row if tuple(r) == old_row else r)

        write_csv(path, after)
        push_undo(path, before)

        await update.message.reply_text("✏️ Entry updated.")
        return

    # =====================
    # DATE CONTEXT
    # =====================
    d = parse_date(lower)
    if d:
        global CURRENT_LOG_DATE
        CURRENT_LOG_DATE = d
        await update.message.reply_text(f"📅 Date set to {d.strftime('%d %b')}")
        return

    # =====================
    # LOG EVENT
    # =====================
    if parsed:
        event, values = parsed
        before = read_csv(EVENTS_FILE)
        rows = before.copy()
        logged = []
        now = datetime.datetime.now()

        if event == "feed":
            i = 0
            while i < len(values):
                t = parse_time(values[i])
                if t > now:
                    await update.message.reply_text("⏳ Cannot log future time.")
                    return

                ml = DEFAULT_FEED_ML
                if i + 1 < len(values) and values[i + 1].lower().endswith("ml"):
                    ml = int(values[i + 1][:-2])
                    i += 1

                rows.append([
                    t.strftime("%Y-%m-%d %H:%M"),
                    user,
                    "feed",
                    str(ml)
                ])
                logged.append(f"{t.strftime('%I:%M %p')} ({ml}ml)")
                i += 1

        else:
            for v in values:
                t = parse_time(v)
                if t > now:
                    await update.message.reply_text("⏳ Cannot log future time.")
                    return

                val = "PooPoo" if event == "diaper_poop" else ""
                rows.append([
                    t.strftime("%Y-%m-%d %H:%M"),
                    user,
                    event.replace("_poop", ""),
                    val
                ])
                logged.append(t.strftime("%I:%M %p"))

        write_csv(EVENTS_FILE, rows)
        push_undo(EVENTS_FILE, before)
        await update.message.reply_text(f"✔️ Logged: {', '.join(logged)}")
        return

    # =====================
    # NOTE (ABSOLUTE FALLBACK)
    # =====================
    before = read_csv(NOTES_FILE)
    write_csv(
        NOTES_FILE,
        before + [[
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            user,
            text
        ]]
    )
    push_undo(NOTES_FILE, before)
    await update.message.reply_text("📝 Saved.")
