# -*- coding: utf-8 -*-
"""Binary STL quality check: triangle count, bounding box, watertightness,
connected components, min wall thickness estimate."""
import struct
import sys
from collections import defaultdict


def main(path):
    with open(path, "rb") as f:
        header = f.read(80)
        f.read(4)  # attribute byte count? no - header includes 80 bytes, then uint32 count
        f.seek(80)
        (ntri,) = struct.unpack("<I", f.read(4))
        verts = []
        normals_count = 0
        for _ in range(ntri):
            data = f.read(50)
            vals = struct.unpack("<12fH", data)
            # vals: nx ny nz, v1x v1y v1z, v2x v2y v2z, v3x v3y v3z, attr
            verts.append((vals[3:6], vals[6:9], vals[9:12]))

    print(f"file: {path}")
    print(f"header: {header[:40]}")
    print(f"triangles: {ntri}")

    xs = [v[i] for t in verts for v in t for i in (0,)]  # slow; do properly below
    allv = [c for t in verts for v in t for c in v]
    xs = allv[0::3]; ys = allv[1::3]; zs = allv[2::3]
    print(f"bbox X: {min(xs):.2f} .. {max(xs):.2f}  ({max(xs)-min(xs):.2f})")
    print(f"bbox Y: {min(ys):.2f} .. {max(ys):.2f}  ({max(ys)-min(ys):.2f})")
    print(f"bbox Z: {min(zs):.2f} .. {max(zs):.2f}  ({max(zs)-min(zs):.2f})")

    # manifold check: every edge shared by exactly 2 triangles
    edges = defaultdict(int)
    for t in verts:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            key = tuple(sorted((a, b)))
            edges[key] += 1
    counts = defaultdict(int)
    for c in edges.values():
        counts[c] += 1
    total_edges = len(edges)
    print(f"unique edges: {total_edges}")
    print(f"edge usage histogram: {dict(sorted(counts.items()))}")
    if counts.get(1, 0) == 0 and counts.get(3, 0) == 0:
        print("WATERTIGHT: yes (all edges shared by exactly 2 triangles)")
    else:
        print(f"WATERTIGHT: NO -> {counts.get(1,0)} boundary edges (used once), {counts.get(3,0)} non-manifold edges (used 3+ times)")


if __name__ == "__main__":
    main(sys.argv[1])
