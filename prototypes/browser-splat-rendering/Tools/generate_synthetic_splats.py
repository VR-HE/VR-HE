#!/usr/bin/env python3
"""Generate synthetic 3D Gaussian Splatting (3DGS) PLY fixtures for the VR-HE browser test.

Everything written here is synthetic: simple procedural shapes that loosely resemble an
equipment room (floor, walls, rack rows with RU-like bands, a wall cabinet). No capture,
photograph or operational headend data is used.

Two fixture families are produced:

* scene_<N>.ply  - the same synthetic room sampled with N splats, for splat-count scaling.
* overlap_A.ply / overlap_B.ply / overlap_AB.ply - two sections that share a band
  (x in [-0.5, 0.5]) where A's sheet is in front of B's. overlap_AB.ply holds A followed by B
  in one file, so a single renderer sorts both sections together; it is the reference image
  for judging whether two separate renderers composite the shared band in the right order.

File format: binary little-endian PLY with the standard 3DGS properties
(x, y, z, f_dc_0..2, opacity, scale_0..2, rot_0..3 and optional f_rest_*). Values follow the
usual training conventions: colour = 0.5 + SH_C0 * f_dc, opacity is a logit, scales are
natural logs and rot_0 is the quaternion w component. Positions are written in the common
3DGS "RUB" frame (right, up, back), so Unity (right, up, forward) z = -file z.

Usage:
    python3 -I generate_synthetic_splats.py --out ../Fixtures/Generated \
        --counts 25000,100000,250000,500000,1000000,2000000 --overlap
"""

import argparse
import json
import math
import os
import random
import sys
from array import array

SH_C0 = 0.28209479177387814
GENERATOR_VERSION = "2"


def logit(p):
    return math.log(p / (1.0 - p))


def to_dc(c):
    return (c - 0.5) / SH_C0


class SplatWriter:
    """Accumulates splats as float32 rows and writes one PLY file."""

    def __init__(self, sh_rest_count=0):
        self.rows = array("f")
        self.count = 0
        self.sh_rest_count = sh_rest_count
        self.row_floats = 14 + sh_rest_count

    def add(self, unity_pos, rgb, opacity, sigmas, rest=None):
        x, y, z = unity_pos
        r, g, b = rgb
        sx, sy, sz = sigmas
        # Unity RUF -> file RUB: negate z. Identity rotation keeps axis-aligned ellipsoids,
        # so the axis flip needs no quaternion change.
        self.rows.extend((x, y, -z, to_dc(r), to_dc(g), to_dc(b), logit(opacity),
                          math.log(sx), math.log(sy), math.log(sz), 1.0, 0.0, 0.0, 0.0))
        if self.sh_rest_count:
            self.rows.extend(rest if rest is not None else (0.0,) * self.sh_rest_count)
        self.count += 1

    def write(self, path, comments):
        if sys.byteorder != "little":
            self.rows.byteswap()
        header = ["ply", "format binary_little_endian 1.0"]
        header += [f"comment {c}" for c in comments]
        header += [f"element vertex {self.count}"]
        for name in ("x", "y", "z", "f_dc_0", "f_dc_1", "f_dc_2", "opacity",
                     "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"):
            header.append(f"property float {name}")
        for i in range(self.sh_rest_count):
            header.append(f"property float f_rest_{i}")
        header.append("end_header")
        with open(path, "wb") as f:
            f.write(("\n".join(header) + "\n").encode("ascii"))
            self.rows.tofile(f)
        if sys.byteorder != "little":
            self.rows.byteswap()


class Rect:
    """A planar rectangle: origin + u*[0,w] + v*[0,h]; thin_axis is the Unity axis normal to it."""

    def __init__(self, name, origin, u_axis, v_axis, w, h, thin_axis, color_fn, opacity=0.92):
        self.name, self.origin, self.u_axis, self.v_axis = name, origin, u_axis, v_axis
        self.w, self.h, self.thin_axis, self.color_fn, self.opacity = w, h, thin_axis, color_fn, opacity

    @property
    def area(self):
        return self.w * self.h

    def point(self, s, t):
        ox, oy, oz = self.origin
        ux, uy, uz = self.u_axis
        vx, vy, vz = self.v_axis
        return (ox + ux * s + vx * t, oy + uy * s + vy * t, oz + uz * s + vz * t)


def sample_rect(writer, rect, n, rng, sh_rest_count):
    """Stratified jittered sampling so coverage stays even at every density."""
    if n <= 0:
        return
    nu = max(1, int(round(math.sqrt(n * rect.w / rect.h))))
    nv = max(1, int(math.ceil(n / nu)))
    du, dv = rect.w / nu, rect.h / nv
    spacing = math.sqrt(du * dv)
    tangent_sigma = 0.6 * spacing
    thin_sigma = max(0.0008, 0.08 * spacing)
    placed = 0
    for j in range(nv):
        for i in range(nu):
            if placed >= n:
                return
            s = (i + rng.random()) * du
            t = (j + rng.random()) * dv
            pos = rect.point(s, t)
            sig = [tangent_sigma, tangent_sigma, tangent_sigma]
            sig[rect.thin_axis] = thin_sigma
            rgb, opacity = rect.color_fn(pos, rect)
            rest = None
            if sh_rest_count:
                # Small deterministic view-dependent tint; values are synthetic.
                rest = tuple((rng.random() - 0.5) * 0.08 for _ in range(sh_rest_count))
            writer.add(pos, rgb, opacity if opacity is not None else rect.opacity, sig, rest)
            placed += 1


# ---------------------------------------------------------------------------------------
# Synthetic room (Unity coordinates, metres; y up, z forward)
# ---------------------------------------------------------------------------------------

def floor_color(p, _rect):
    x, _, z = p
    line = min(abs(x / 0.6 - round(x / 0.6)), abs(z / 0.6 - round(z / 0.6))) * 0.6 < 0.012
    return ((0.36, 0.37, 0.38) if line else (0.63, 0.63, 0.61)), None


def back_wall_color(p, _rect):
    y = p[1]
    if 2.2 <= y <= 2.32:
        return (0.35, 0.35, 0.40), None  # cable-tray-like band
    return (0.80, 0.77, 0.70), None


def side_wall_color(_p, _rect):
    return (0.70, 0.73, 0.76), None


def dark_frame_color(_p, _rect):
    return (0.09, 0.09, 0.11), None


RU = 0.04445
PALETTE = [(0.17, 0.17, 0.19), (0.55, 0.56, 0.58), (0.06, 0.06, 0.07), (0.24, 0.30, 0.42),
           (0.40, 0.40, 0.42)]


def make_rack_front_color(rack_seed):
    """Equipment-like horizontal bands of 1-4 RU with small LED dots; deterministic per rack."""
    rng = random.Random(rack_seed)
    bands = []
    y = 0.10
    while y < 1.90:
        units = rng.choice((1, 1, 2, 2, 3, 4))
        top = min(1.90, y + units * RU)
        filled = rng.random() > 0.18
        bands.append((y, top, rng.choice(PALETTE) if filled else None, rng.random() > 0.4))
        y = top

    def color(p, rect):
        x, yy, _ = p
        local_x = (x - rect.origin[0]) if rect.u_axis[0] > 0 else (rect.origin[0] - x)
        for (y0, y1, c, led) in bands:
            if y0 <= yy < y1:
                if c is None:
                    return (0.03, 0.03, 0.035), None  # empty RU: dark gap
                if led and 0.05 < local_x < 0.075 and (yy - y0) < 0.025:
                    return ((0.15, 0.95, 0.30) if (int(y0 * 1000) % 3) else (1.0, 0.70, 0.10)), 0.98
                return c, None
        return dark_frame_color(p, rect)

    return color


def cabinet_door_color(p, _rect):
    x, y, _ = p
    if 2.15 < x < 2.2 and 1.25 < y < 1.5:
        return (0.12, 0.12, 0.12), None  # handle
    return (0.52, 0.54, 0.57), None


def build_room_rects():
    rects = [
        Rect("floor", (-4.0, 0.0, -3.0), (1, 0, 0), (0, 0, 1), 8.0, 6.0, 1, floor_color),
        Rect("back_wall", (-4.0, 0.0, 3.0), (1, 0, 0), (0, 1, 0), 8.0, 3.0, 2, back_wall_color),
        Rect("left_wall", (-4.0, 0.0, -3.0), (0, 0, 1), (0, 1, 0), 6.0, 3.0, 0, side_wall_color),
    ]
    rack_index = 0
    for row_z, faces_neg_z in ((-1.2, True), (1.0, False)):
        for i in range(5):
            xc = -1.6 + i * 0.62
            x0, x1 = xc - 0.3, xc + 0.3
            z0, z1 = row_z - 0.5, row_z + 0.5
            front_z = z0 if faces_neg_z else z1
            back_z = z1 if faces_neg_z else z0
            front = make_rack_front_color(1000 + rack_index)
            # Front face: u runs along +x when facing -z, -x when facing +z (keeps LEDs on the left).
            if faces_neg_z:
                rects.append(Rect(f"rack{rack_index}_front", (x0, 0.0, front_z), (1, 0, 0), (0, 1, 0),
                                  0.6, 2.0, 2, front))
            else:
                rects.append(Rect(f"rack{rack_index}_front", (x1, 0.0, front_z), (-1, 0, 0), (0, 1, 0),
                                  0.6, 2.0, 2, front))
            rects.append(Rect(f"rack{rack_index}_back", (x0, 0.0, back_z), (1, 0, 0), (0, 1, 0),
                              0.6, 2.0, 2, dark_frame_color))
            rects.append(Rect(f"rack{rack_index}_left", (x0, 0.0, z0), (0, 0, 1), (0, 1, 0),
                              1.0, 2.0, 0, dark_frame_color))
            rects.append(Rect(f"rack{rack_index}_right", (x1, 0.0, z0), (0, 0, 1), (0, 1, 0),
                              1.0, 2.0, 0, dark_frame_color))
            rects.append(Rect(f"rack{rack_index}_top", (x0, 2.0, z0), (1, 0, 0), (0, 0, 1),
                              0.6, 1.0, 1, dark_frame_color))
            rack_index += 1
    # Wall cabinet (door face plus sides) on the back wall.
    rects += [
        Rect("cabinet_door", (1.5, 0.8, 2.75), (1, 0, 0), (0, 1, 0), 0.8, 1.2, 2, cabinet_door_color),
        Rect("cabinet_left", (1.5, 0.8, 2.75), (0, 0, 1), (0, 1, 0), 0.25, 1.2, 0, side_wall_color),
        Rect("cabinet_right", (2.3, 0.8, 2.75), (0, 0, 1), (0, 1, 0), 0.25, 1.2, 0, side_wall_color),
        Rect("cabinet_top", (1.5, 2.0, 2.75), (1, 0, 0), (0, 0, 1), 0.8, 0.25, 1, side_wall_color),
    ]
    return rects


def allocate(rects, total):
    area = sum(r.area for r in rects)
    counts = [int(total * r.area / area) for r in rects]
    counts[0] += total - sum(counts)  # remainder to the floor
    return counts


def generate_scene(total, sh_degree, seed):
    sh_rest = {0: 0, 1: 9, 2: 24, 3: 45}[sh_degree]
    rng = random.Random(seed)
    writer = SplatWriter(sh_rest)
    rects = build_room_rects()
    for rect, n in zip(rects, allocate(rects, total)):
        sample_rect(writer, rect, n, rng, sh_rest)
    assert writer.count == total, (writer.count, total)
    return writer


# ---------------------------------------------------------------------------------------
# Overlap sections: two sections sharing a band, built so that per-object ordering fails
# ---------------------------------------------------------------------------------------
#
# Section A models a large existing capture: a red sheet at z = 0.0 plus a far backdrop at
# z = 3.0, which pushes A's bounds centre away from the camera. Section B models a small
# rescanned area: one blue sheet at z = 0.3. In the shared band (x in [-0.5, 0.5]) A's red
# sheet is physically in FRONT of B's blue sheet for a camera at negative z.
#
# Correct per-splat ordering (one sort over both sections) shows red over blue in the band.
# A renderer that orders whole objects by bounds-centre distance draws B (nearer centre) last
# and shows blue over red there: the colour flip makes the error unambiguous. Forcing A to
# draw last fixes the band but paints A's backdrop over B's exclusive region, so no single
# whole-object order is correct for both.

OVERLAP_SPACING = 0.015
SECTION_A = {"sheets": [
    {"name": "A_front", "color": (0.90, 0.15, 0.10), "opacity": 0.8, "x": (-1.5, 0.5), "y": (0.5, 2.0), "z": 0.0},
    # Wide enough that, from the test camera, it lies behind all of B's exclusive region.
    {"name": "A_backdrop", "color": (0.45, 0.32, 0.30), "opacity": 0.95, "x": (-3.5, 3.5), "y": (0.0, 2.5), "z": 3.0},
]}
SECTION_B = {"sheets": [
    {"name": "B_sheet", "color": (0.10, 0.25, 0.95), "opacity": 0.8, "x": (-0.5, 1.5), "y": (0.5, 2.0), "z": 0.3},
]}


def add_section(writer, section, rng):
    for sheet in section["sheets"]:
        x0, x1 = sheet["x"]
        y0, y1 = sheet["y"]
        rect = Rect(sheet["name"], (x0, y0, sheet["z"]), (1, 0, 0), (0, 1, 0), x1 - x0, y1 - y0, 2,
                    lambda _p, _r, c=sheet["color"], a=sheet["opacity"]: (c, a), sheet["opacity"])
        n = int(round(rect.area / (OVERLAP_SPACING * OVERLAP_SPACING)))
        sample_rect(writer, rect, n, rng, 0)


def generate_overlap(seed):
    a, b, ab = SplatWriter(), SplatWriter(), SplatWriter()
    add_section(a, SECTION_A, random.Random(seed))
    add_section(b, SECTION_B, random.Random(seed + 1))
    # Same random streams, so AB is exactly A's splats followed by B's splats.
    add_section(ab, SECTION_A, random.Random(seed))
    add_section(ab, SECTION_B, random.Random(seed + 1))
    return a, b, ab


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True)
    parser.add_argument("--counts", default="25000,100000,250000,500000,1000000,2000000")
    parser.add_argument("--sh3-counts", default="", help="extra scene sizes written with SH degree 3")
    parser.add_argument("--overlap", action="store_true")
    parser.add_argument("--seed", type=int, default=20261110)
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    manifest = {"generator": "generate_synthetic_splats.py", "generator_version": GENERATOR_VERSION,
                "seed": args.seed, "synthetic": True, "files": []}
    common = [f"VR-HE synthetic fixture; generator v{GENERATOR_VERSION}; seed {args.seed}; no operational data"]

    jobs = [(int(c), 0) for c in args.counts.split(",") if c.strip()]
    jobs += [(int(c), 3) for c in args.sh3_counts.split(",") if c.strip()]
    for count, sh in jobs:
        name = f"scene_{count}.ply" if sh == 0 else f"scene_{count}_sh{sh}.ply"
        writer = generate_scene(count, sh, args.seed)
        path = os.path.join(args.out, name)
        writer.write(path, common + [f"family scene; splats {count}; sh_degree {sh}"])
        manifest["files"].append({"name": name, "splats": writer.count, "sh_degree": sh,
                                  "bytes": os.path.getsize(path), "family": "scene"})
        print(f"wrote {name}: {writer.count} splats, {os.path.getsize(path)} bytes")

    if args.overlap:
        a, b, ab = generate_overlap(args.seed)
        for name, writer, note in (("overlap_A.ply", a, "section A"), ("overlap_B.ply", b, "section B"),
                                   ("overlap_AB.ply", ab, "section A then section B")):
            path = os.path.join(args.out, name)
            writer.write(path, common + [f"family overlap; {note}"])
            manifest["files"].append({"name": name, "splats": writer.count, "sh_degree": 0,
                                      "bytes": os.path.getsize(path), "family": "overlap"})
            print(f"wrote {name}: {writer.count} splats")
        manifest["overlap"] = {"section_a_count": a.count, "section_b_count": b.count,
                               "section_a": SECTION_A, "section_b": SECTION_B,
                               "shared_band_x": [-0.5, 0.5],
                               "expected_front_view_band": "red (A, z=0.0) over blue (B, z=0.3)"}

    with open(os.path.join(args.out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("wrote manifest.json")


if __name__ == "__main__":
    main()
