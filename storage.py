import csv

ACTION_HISTORY = []

def read_csv(path):
    try:
        with open(path, newline="") as f:
            return list(csv.reader(f))
    except FileNotFoundError:
        return []

def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)

def push_undo(path, before_rows):
    ACTION_HISTORY.append({
        "path": path,
        "before": before_rows
    })

def undo_last():
    if not ACTION_HISTORY:
        return False

    action = ACTION_HISTORY.pop()
    write_csv(action["path"], action["before"])
    return True
