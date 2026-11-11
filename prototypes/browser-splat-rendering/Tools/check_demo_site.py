#!/usr/bin/env python3
"""Check that the interactive demo's proxies line up with the synthetic room.

Compares Assets/InteractiveDemo/Data/demo-site.json with the geometry that
Tools/generate_synthetic_splats.py uses to place splats (build_room_rects): every rack anchor
must cover exactly one generated rack box, the visible walls and the wall cabinet must match
their generated planes, identifiers must be unique and well formed, and the spawn point must be
inside the room and clear of every proxy. Prints each check; exit code 1 on any failure.

The splat itself is never used for collision or picking. This check is what ties the
invisible proxies to what the tester sees.
"""

import importlib.util
import json
import os
import re
import sys

sys.dont_write_bytecode = True  # loading the generator by path must not leave __pycache__ behind

TOOLS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(TOOLS)
SITE = os.path.join(PROJECT, "Assets", "InteractiveDemo", "Data", "demo-site.json")
ID = re.compile(r"^(site|rec|anc)-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
TOLERANCE = 1e-6
PLAYER_RADIUS = 0.25


def load_generator():
    spec = importlib.util.spec_from_file_location("vrhe_generator", os.path.join(TOOLS, "generate_synthetic_splats.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rect_box(rects):
    points = []
    for r in rects:
        for s, t in ((0, 0), (r.w, 0), (0, r.h), (r.w, r.h)):
            points.append(r.point(s, t))
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    return lo, hi


def box(center, size):
    return [c - s / 2 for c, s in zip(center, size)], [c + s / 2 for c, s in zip(center, size)]


def same(a, b):
    return all(abs(x - y) <= TOLERANCE for x, y in zip(a[0] + a[1], b[0] + b[1]))


def main():
    with open(SITE, encoding="utf-8") as f:
        site = json.load(f)
    gen = load_generator()
    rects = gen.build_room_rects()
    failures = []

    def check(name, ok, detail=""):
        print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
        if not ok:
            failures.append(name)

    ids = [site["siteId"]] + [r["recordId"] for r in site["records"]] + [a["anchorId"] for a in site["anchors"]]
    check("identifiers are prefixed UUIDs", all(ID.match(i) for i in ids))
    check("identifiers are unique", len(ids) == len(set(ids)))
    records = {r["recordId"]: r for r in site["records"]}
    check("every anchor points to a record", all(a["recordId"] in records for a in site["anchors"]))
    check("names are not used as identifiers", not ({r["name"] for r in site["records"]} & set(ids)))

    racks = sorted({r.name.split("_")[0] for r in rects if r.name.startswith("rack")}, key=lambda n: int(n[4:]))
    check("ten generated racks and ten rack anchors", len(racks) == 10 and len(site["anchors"]) == 10)
    for index, rack in enumerate(racks):
        generated = rect_box([r for r in rects if r.name.startswith(rack + "_")])
        anchor = site["anchors"][index]
        record = records[anchor["recordId"]]
        proxy = box(anchor["center"], anchor["size"])
        check(f"{record['name']} proxy matches generated {rack}", same(proxy, generated),
              f"proxy {proxy}, generated {generated}")
        front = [r for r in rects if r.name == rack + "_front"][0]
        faces = "-z" if abs(front.origin[2] - generated[0][2]) <= TOLERANCE else "+z"
        check(f"{record['name']} front faces {faces}", anchor["frontFacing"] == faces)

    obstacles = {o["name"]: o for o in site["obstacles"]}
    cabinet = rect_box([r for r in rects if r.name.startswith("cabinet_")])
    cab = box(obstacles["wall cabinet (not selectable in this demo)"]["center"],
              obstacles["wall cabinet (not selectable in this demo)"]["size"])
    check("wall cabinet proxy spans the generated cabinet",
          all(abs(cab[0][i] - cabinet[0][i]) <= TOLERANCE for i in range(3)) and
          all(abs(cab[1][i] - cabinet[1][i]) <= TOLERANCE for i in range(2)) and cab[1][2] >= cabinet[1][2],
          f"proxy {cab}, generated {cabinet}")
    floor = box(obstacles["floor"]["center"], obstacles["floor"]["size"])
    check("floor proxy top is the generated floor (y = 0) and covers it",
          abs(floor[1][1]) <= TOLERANCE and floor[0][0] <= -4 and floor[1][0] >= 4 and floor[0][2] <= -3 and floor[1][2] >= 3)
    back = box(obstacles["back wall"]["center"], obstacles["back wall"]["size"])
    check("back wall proxy starts at the generated wall (z = 3)", abs(back[0][2] - 3.0) <= TOLERANCE)
    left = box(obstacles["left wall"]["center"], obstacles["left wall"]["size"])
    check("left wall proxy ends at the generated wall (x = -4)", abs(left[1][0] + 4.0) <= TOLERANCE)

    feet = site["spawn"]["feet"]
    inside = -4 + PLAYER_RADIUS < feet[0] < 4 - PLAYER_RADIUS and -3 + PLAYER_RADIUS < feet[2] < 3 - PLAYER_RADIUS
    clear = True
    for item in site["anchors"] + [o for o in site["obstacles"] if o["name"] != "floor"]:
        lo, hi = box(item["center"], item["size"])
        if lo[0] - PLAYER_RADIUS < feet[0] < hi[0] + PLAYER_RADIUS and lo[2] - PLAYER_RADIUS < feet[2] < hi[2] + PLAYER_RADIUS:
            clear = False
    check("spawn point is inside the room and clear of proxies", inside and clear and abs(feet[1]) <= TOLERANCE,
          f"feet {feet}")
    print(f"\n{'all checks passed' if not failures else str(len(failures)) + ' check(s) failed'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
