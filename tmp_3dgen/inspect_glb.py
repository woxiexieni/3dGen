import json
import struct
import sys
import os

path = sys.argv[1]
outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)

with open(path, "rb") as f:
    data = f.read()

magic, version, length = struct.unpack_from("<III", data, 0)
print("GLB magic=0x%x version=%d size=%.1fMB" % (magic, version, len(data) / 1048576))

offset = 12
g = None
bin_chunk = None
while offset < length:
    clen, ctype = struct.unpack_from("<II", data, offset)
    offset += 8
    payload = data[offset:offset + clen]
    if ctype == 0x4E4F534A:
        g = json.loads(payload.decode("utf-8"))
    elif ctype == 0x004E4942:
        bin_chunk = payload
    offset += clen

print("\n=== overview ===")
for k in ("meshes", "materials", "images", "textures", "nodes"):
    print("%-10s %d" % (k, len(g.get(k, []))))

for i, m in enumerate(g.get("meshes", [])):
    for p in m.get("primitives", []):
        attrs = list(p.get("attributes", {}).keys())
        tri = 0
        if p.get("indices") is not None:
            tri = g["accessors"][p["indices"]]["count"] // 3
        print("mesh[%d] name=%s attrs=%s tris=%d" % (i, m.get("name"), attrs, tri))

print("\n=== materials ===")
for i, mat in enumerate(g.get("materials", [])):
    pbr = mat.get("pbrMetallicRoughness", {})
    print("[%d] %s baseColorTex=%s" % (i, mat.get("name"), pbr.get("baseColorTexture")))

print("\n=== images ===")
for i, img in enumerate(g.get("images", [])):
    bv = img.get("bufferView")
    if bv is None:
        continue
    view = g["bufferViews"][bv]
    start = view.get("byteOffset", 0)
    ln = view["byteLength"]
    mime = img.get("mimeType", "")
    ext = ".png" if "png" in mime else ".jpg"
    out = os.path.join(outdir, "texture_%d%s" % (i, ext))
    with open(out, "wb") as f:
        f.write(bin_chunk[start:start + ln])
    # 读 PNG 尺寸
    dims = ""
    head = bin_chunk[start:start + 33]
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", head[16:24])
        dims = "%dx%d" % (w, h)
    print("[%d] %s %s bytes=%d %s -> %s" % (i, img.get("name"), mime, ln, dims, out))

# UV 覆盖率分析
print("\n=== UV analysis ===")
accs = g["accessors"]
bvs = g["bufferViews"]
total_uv_area = 0.0
uv_bbox = [1e9, 1e9, -1e9, -1e9]
for m in g.get("meshes", []):
    for p in m.get("primitives", []):
        attrs = p.get("attributes", {})
        if "TEXCOORD_0" not in attrs:
            print("no TEXCOORD_0")
            continue
        acc = accs[attrs["TEXCOORD_0"]]
        print("uv accessor count=%d type=%s" % (acc["count"], acc["type"]))
        bv = bvs[acc["bufferView"]]
        start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        count = acc["count"]
        comp = {5126: 4, 5123: 2}[acc["componentType"]]
        stride = bv.get("byteStride") or comp * 2
        us = []
        vs = []
        for k in range(count):
            o = start + k * stride
            u = struct.unpack_from("<f", bin_chunk, o)[0]
            v = struct.unpack_from("<f", bin_chunk, o + 4)[0]
            us.append(u)
            vs.append(v)
        if us:
            print("u range %.3f..%.3f  v range %.3f..%.3f" % (min(us), max(us), min(vs), max(vs)))
