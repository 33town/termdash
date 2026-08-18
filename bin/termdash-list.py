#!/usr/bin/env python3
"""List recent Claude Code sessions across all projects for termdash.

Outputs TSV: display \t session_id \t cwd
Sorted by last activity descending. Optional argv[1] filters by
case-insensitive substring match on the session name (the name you
gave the session via /rename, or Claude's auto-generated title if you
never renamed it).

Customize:
- LIMIT / $TERMDASH_LIMIT: how many sessions to list (default 20)
- NAME_COL_WIDTH: width of the name column in the printed table
"""
import json
import sys
import glob
import os

LIMIT = int(os.environ.get("TERMDASH_LIMIT", "20"))
NAME_COL_WIDTH = int(os.environ.get("TERMDASH_NAME_WIDTH", "42"))


def session_info(path):
    session_id = os.path.basename(path)[: -len(".jsonl")]
    custom_title = None
    ai_title = None
    cwd = None
    last_ts = None

    with open(path, "r", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue

            t = d.get("type")
            if t == "custom-title":
                custom_title = d.get("customTitle")
            elif t == "ai-title":
                ai_title = d.get("aiTitle")

            if d.get("cwd") and cwd is None:
                cwd = d.get("cwd")

            ts = d.get("timestamp")
            if ts:
                last_ts = ts

    if last_ts is None:
        last_ts_epoch = os.path.getmtime(path)
    else:
        # ISO 8601 -> epoch, tolerate trailing 'Z'
        try:
            from datetime import datetime

            last_ts_epoch = datetime.fromisoformat(
                last_ts.replace("Z", "+00:00")
            ).timestamp()
        except ValueError:
            last_ts_epoch = os.path.getmtime(path)

    name = custom_title or ai_title or "(untitled)"
    return {
        "session_id": session_id,
        "name": name,
        "cwd": cwd or "",
        "last_ts_epoch": last_ts_epoch,
        "last_ts": last_ts or "",
    }


def display_width(ch):
    # treat CJK / fullwidth-ish codepoints as width 2
    return 2 if ord(ch) > 0x2E7F else 1


def pad_name(name, width):
    w = sum(display_width(c) for c in name)
    if w <= width:
        return name + " " * (width - w)

    acc = 0
    out = []
    for c in name:
        acc += display_width(c)
        if acc > width - 3:
            out.append("...")
            break
        out.append(c)
    truncated = "".join(out)
    return truncated + " " * max(0, width - sum(display_width(c) for c in truncated))


def main():
    query = sys.argv[1].lower() if len(sys.argv) > 1 else None

    files = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
    sessions = []
    for f in files:
        try:
            info = session_info(f)
        except Exception:
            continue
        if query and query not in info["name"].lower():
            continue
        sessions.append(info)

    sessions.sort(key=lambda s: s["last_ts_epoch"], reverse=True)
    sessions = sessions[:LIMIT]

    for s in sessions:
        display_time = s["last_ts"][:16].replace("T", " ") if s["last_ts"] else ""
        project = os.path.basename(s["cwd"]) if s["cwd"] else "?"
        name_col = pad_name(s["name"], NAME_COL_WIDTH)
        display = f"{name_col} {display_time:<16} {project}"
        print("\t".join([display, s["session_id"], s["cwd"]]))


if __name__ == "__main__":
    main()
