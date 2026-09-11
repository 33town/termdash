#!/usr/bin/env python3
"""List recent Claude Code sessions across all projects for termdash.

Outputs TSV: display \t session_id \t cwd \t tty
Sorted by last activity descending. Optional argv[1] filters by
case-insensitive substring match on any of:
- the session name (the name you gave the session via /rename, or
  Claude's auto-generated title if you never renamed it)
- the session ID (full or prefix)
- the peer name of a running session (what ListAgents / SendMessage
  call it, e.g. "amazon-brain-2c")
- the claude.ai bridge session ID of a running session ("session_01...")
tty is non-empty only when the session is running right now.

Customize:
- LIMIT / $TERMDASH_LIMIT: how many sessions to list (default 20)
- NAME_COL_WIDTH: width of the name column in the printed table
"""
import json
import sys
import glob
import os
import subprocess

LIMIT = int(os.environ.get("TERMDASH_LIMIT", "20"))
NAME_COL_WIDTH = int(os.environ.get("TERMDASH_NAME_WIDTH", "42"))
PROJECT_COL_WIDTH = 16


def live_sessions():
    """Map sessionId -> {peer, bridge, tty} for Claude processes still running.

    ~/.claude/sessions/<pid>.json is written by each running Claude Code
    process; "name" there is the peer name other sessions see in ListAgents.
    Files can outlive their process, so keep only pids that are still a
    running `claude`.
    """
    entries = []
    for f in glob.glob(os.path.expanduser("~/.claude/sessions/*.json")):
        try:
            with open(f) as fh:
                d = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if d.get("sessionId") and d.get("pid"):
            entries.append(d)
    if not entries:
        return {}

    pids = ",".join(str(e["pid"]) for e in entries)
    ps = subprocess.run(
        ["ps", "-o", "pid=,tty=,comm=", "-p", pids], capture_output=True, text=True
    ).stdout
    alive = {}
    for line in ps.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and os.path.basename(parts[2]) == "claude":
            alive[int(parts[0])] = "" if parts[1] == "??" else parts[1]

    result = {}
    for e in entries:
        if e["pid"] not in alive:
            continue
        result[e["sessionId"]] = {
            "peer": e.get("name") or "",
            "bridge": e.get("bridgeSessionId") or "",
            "tty": alive[e["pid"]],
        }
    return result


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
    live = live_sessions()

    files = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
    sessions = []
    for f in files:
        try:
            info = session_info(f)
        except Exception:
            continue
        running = live.get(info["session_id"])
        info["running"] = running is not None
        info["peer"] = running["peer"] if running else ""
        info["tty"] = running["tty"] if running else ""
        if query:
            haystack = [info["name"], info["session_id"], info["peer"]]
            if running:
                haystack.append(running["bridge"])
            if not any(query in h.lower() for h in haystack):
                continue
        sessions.append(info)

    sessions.sort(key=lambda s: s["last_ts_epoch"], reverse=True)
    sessions = sessions[:LIMIT]

    for s in sessions:
        display_time = s["last_ts"][:16].replace("T", " ") if s["last_ts"] else ""
        project = os.path.basename(s["cwd"]) if s["cwd"] else "?"
        mark = "●" if s["running"] else " "
        name_col = pad_name(s["name"], NAME_COL_WIDTH)
        project_col = pad_name(project, PROJECT_COL_WIDTH)
        display = (
            f"{mark} {name_col} {display_time:<16} {project_col} "
            f"{s['session_id'][:8]}  {s['peer']}"
        )
        print("\t".join([display, s["session_id"], s["cwd"], s["tty"]]))


if __name__ == "__main__":
    main()
