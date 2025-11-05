#!/usr/bin/env python3
"""
cowrie_bridge.py
Simple tailer for Cowrie JSON log. Reads new JSON-lines from cowrie log,
extracts useful fields and writes an events JSON file that the browser can fetch.

Configure LOG_PATH to your cowrie JSON log (e.g. /opt/cowrie/var/log/cowrie/cowrie.json)
Output files:
 - /opt/cowrie-bridge/out/cowrie_events.json  (machine readable)
 - /opt/cowrie-bridge/out/cowrie_events.html  (human readable - appended)
"""

import time
import json
import os
import errno
from pathlib import Path

# ==== CONFIG ====
LOG_PATH = "/opt/cowrie/var/log/cowrie/cowrie.json"   # adjust to your cowrie log path
OUT_DIR = "/opt/cowrie-bridge/out"
OUT_JSON = os.path.join(OUT_DIR, "cowrie_events.json")
OUT_HTML = os.path.join(OUT_DIR, "cowrie_events.html")
MAX_EVENTS = 1000          # cap kept in memory / output
POLL_INTERVAL = 0.5        # seconds
# =================

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

def atomic_write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp, path)

def parse_event(line):
    """
    Parse a cowrie JSON-line. Return a compact dict of fields we care about,
    or None if the line isn't JSON or not an event we want.
    """
    try:
        obj = json.loads(line)
    except Exception:
        return None

    # Cowrie logs many event types; pick ones commonly useful
    event_type = obj.get("event")
    timestamp = obj.get("timestamp") or obj.get("time") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out = {
        "event": event_type,
        "timestamp": timestamp,
        "raw": obj
    }

    # Examples of extracting important details if present
    if event_type in ("cowrie.login.success", "cowrie.login.failed", "cowrie.session.connect", "cowrie.session.closed"):
        out["src_ip"] = obj.get("src_ip") or obj.get("peer", {}).get("host")
        out["username"] = obj.get("username") or obj.get("user")
        out["password"] = obj.get("password") or obj.get("password_attempt")
        out["session"] = obj.get("session") or obj.get("session", {}).get("session")
    # for command executed
    if event_type == "cowrie.command.input":
        out["session"] = obj.get("session")
        out["input"] = obj.get("input")
    # for file downloads / uploads
    if event_type and "download" in event_type or "upload" in event_type:
        out["url"] = obj.get("url")
        out["filename"] = obj.get("filename") or obj.get("path")

    return out

def tail_file(path):
    """
    Yields lines as they appear in the file (like tail -F).
    Handles file truncation/rotation by checking inode/size.
    """
    last_inode = None
    f = None
    while True:
        try:
            st = os.stat(path)
        except OSError as e:
            if e.errno in (errno.ENOENT, errno.EACCES):
                # file not there yet; wait and retry
                time.sleep(1.0)
                continue
            raise

        inode = (st.st_ino, st.st_dev)
        if f is None or inode != last_inode:
            # (re)open file
            if f:
                f.close()
            f = open(path, "r", encoding="utf-8", errors="ignore")
            # start at end so we only get new events
            f.seek(0, os.SEEK_END)
            last_inode = inode

        line = f.readline()
        if not line:
            # no new line yet
            time.sleep(POLL_INTERVAL)
            continue
        yield line.rstrip("\n")

def main():
    events = []  # list of parsed events (most recent last)
    print("Cowrie bridge starting, tailing:", LOG_PATH)
    try:
        for line in tail_file(LOG_PATH):
            parsed = parse_event(line)
            if not parsed:
                continue
            # keep only relevant fields to keep JSON small
            compact = {
                "ts": parsed.get("timestamp"),
                "evt": parsed.get("event"),
                "ip": parsed.get("src_ip"),
                "user": parsed.get("username"),
                "pw": parsed.get("password"),
            }
            # add other fields if present
            if "input" in parsed:
                compact["cmd"] = parsed["input"]
            if "url" in parsed:
                compact["url"] = parsed["url"]

            # append and limit size
            events.append(compact)
            if len(events) > MAX_EVENTS:
                events = events[-MAX_EVENTS:]

            # write JSON file atomically
            try:
                atomic_write(OUT_JSON, json.dumps({"events": events}, ensure_ascii=False, indent=2))
            except Exception as e:
                print("Error writing JSON:", e)

            # append a human readable line to OUT_HTML (optional)
            try:
                with open(OUT_HTML, "a", encoding="utf-8") as h:
                    h.write(f"{compact.get('ts')} {compact.get('ip')} {compact.get('evt')} user={compact.get('user')} cmd={compact.get('cmd','')}\n")
            except Exception:
                pass

    except KeyboardInterrupt:
        print("Stopping cowrie bridge.")
    except Exception as e:
        print("Fatal error:", e)

if __name__ == "__main__":
    main()
