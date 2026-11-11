#!/usr/bin/env python3
"""Audit a running subagent fan-out: is anyone idle, looping, or done?

Usage:
    python audit_agents.py --root C:/Users/<user>/AppData/Local/hermes/cache/delegation/live \
        --expect deleg_ab12:0=out/agent-a.md deleg_ab12:1=out/agent-b.md

With no --expect, it audits every task-*.log under --root and skips the
"output written?" column. Read-only: it never touches the children.

Columns:
    name      deleg_xxx:task-N label
    window    first -> last timestamp in the transcript
    age       seconds since the last line (large = possibly stalled)
    tools     number of tool calls
    top       highest repeat count of one command signature (loop tell)
    md        whether the expected output file exists

A real loop shows top in the dozens with an identical signature; normal
iteration varies the arguments and stays in single digits.
"""
import argparse
import glob
import os
import re
import time

TS = re.compile(r"^(\d\d:\d\d:\d\d)")
TOOL = "tool     | ->"


def signature(line: str) -> str:
    """Normalise a tool call so identical commands collapse to one key."""
    body = line.split("->", 1)[-1]
    body = re.sub(r"\d+", "N", body)
    return body[:70].strip()


def audit(path: str):
    lines = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    stamps = [m.group(1) for l in lines if (m := TS.match(l))]
    tools = [l for l in lines if TOOL in l]
    sigs = [signature(l) for l in tools]
    top = max((sigs.count(s) for s in set(sigs)), default=0)
    age = "?"
    if stamps:
        try:
            last = time.strptime(stamps[-1], "%H:%M:%S")
            now = time.localtime()
            age = int((now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec)
                      - (last.tm_hour * 3600 + last.tm_min * 60 + last.tm_sec)) % 86400
        except ValueError:
            pass
    return {
        "window": f"{stamps[0] if stamps else '?'}->{stamps[-1] if stamps else '?'}",
        "age": age,
        "tools": len(tools),
        "top": top,
        "tail": [l[:90] for l in tools[-2:]],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--expect", nargs="*", default=[],
                    help="deleg_id:task_index=path/to/output.md")
    args = ap.parse_args()

    expected = {}
    for spec in args.expect:
        key, _, out = spec.partition("=")
        expected[key] = out

    logs = sorted(glob.glob(os.path.join(args.root, "deleg_*", "task-*.log")))
    if not logs:
        print("no transcripts under", args.root)
        return

    print(f"{'name':22} {'window':19} {'age':>5} {'tools':>5} {'top':>4}  md")
    for path in logs:
        deleg = os.path.basename(os.path.dirname(path))
        task = os.path.basename(path).replace("task-", "").replace(".log", "")
        name = f"{deleg[-8:]}:{task}"
        a = audit(path)
        out = expected.get(f"{deleg}:{task}")
        md = "?" if out is None else ("VAR" if os.path.exists(out) else "yok")
        print(f"{name:22} {a['window']:19} {str(a['age']):>5} {a['tools']:>5} {a['top']:>4}  {md}")
        if a["top"] >= 15:
            print(f"    LOOP SUSPECT top={a['top']}: {a['tail'][-1] if a['tail'] else ''}")


if __name__ == "__main__":
    main()
