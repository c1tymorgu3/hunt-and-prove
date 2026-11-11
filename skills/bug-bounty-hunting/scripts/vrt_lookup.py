#!/usr/bin/env python3
"""Look up Bugcrowd VRT categories and the priority each one maps to.

Usage:
    python vrt_lookup.py                      # list categories
    python vrt_lookup.py denial               # every path containing 'denial'
    python vrt_lookup.py --refresh denial     # re-download the taxonomy first

Only variants carry a priority. A subcategory can carry one directly, but a subcategory with no
priority of its own inherits nothing: picking it gives the triager no suggested severity, which is
how a real bug ends up unclassified.
"""

import json
import os
import sys
import urllib.request

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vrt.json")
URL = "https://bugcrowd.com/vrt.json"


def load(refresh=False):
    if refresh or not os.path.exists(CACHE):
        req = urllib.request.Request(URL, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        with open(CACHE, "wb") as f:
            f.write(data)
    with open(CACHE, encoding="utf-8") as f:
        return json.load(f)


def walk(node, path, out):
    here = path + [node.get("name", "?")]
    prio = node.get("priority")
    if prio:
        out.append((" > ".join(here), prio, node.get("type", "")))
    for child in node.get("children") or []:
        walk(child, here, out)


def flatten(doc):
    out = []
    for cat in doc["content"]:
        walk(cat, [], out)
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    refresh = "--refresh" in sys.argv
    doc = load(refresh)
    rows = flatten(doc)

    if not args:
        print("VRT release:", doc.get("metadata", {}).get("release_date"))
        print("nodes with a priority:", len(rows))
        for cat in doc["content"]:
            print(" ", cat["name"])
        return

    needle = " ".join(args).lower()
    hits = [r for r in rows if needle in r[0].lower()]
    if not hits:
        print("no node matches %r" % needle)
        return
    for path, prio, kind in sorted(hits, key=lambda r: (r[1], r[0])):
        print("P%d  %-14s %s" % (prio, kind, path))


if __name__ == "__main__":
    main()
