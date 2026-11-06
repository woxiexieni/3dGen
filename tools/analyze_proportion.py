"""按高度切片分析手办模型的人体比例（STL/二进制）。
输出：bbox、头身比、各高度层的截面宽度，用于判断模型比例是否失真。
用法: python analyze_proportion.py model.stl
"""
import struct
import sys

import numpy as np


def load_stl(path):
    with open(path, "rb") as f:
        header = f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        data = np.frombuffer(f.read(n * 50), dtype=np.uint8).reshape(n, 50)
    tris = data[:, 12:48].copy().view("<f4").reshape(n, 3, 3)
    return tris.astype(np.float64)


def main(path):
    tris = load_stl(path)
    verts = tris.reshape(-1, 3)
    lo, hi = verts.min(axis=0), verts.max(axis=0)
    size = hi - lo
    print("面片数 %d  顶点数 %d" % (len(tris), len(verts)))
    print("bbox  X %.4f..%.4f (%.4f)  Y %.4f..%.4f (%.4f)  Z %.4f..%.4f (%.4f)"
          % (lo[0], hi[0], size[0], lo[1], hi[1], size[1], lo[2], hi[2], size[2]))

    # 假设 Z 为高度轴（取最长轴）
    axis = int(np.argmax(size))
    other = [i for i in range(3) if i != axis]
    h = verts[:, axis]
    hmin, hmax = h.min(), h.max()
    total = hmax - hmin

    print("\n高度轴 = %s, 总高 %.4f" % ("XYZ"[axis], total))
    print("\n=== 逐层截面（从脚底到头顶，每 4%% 一层）===")
    print("%6s %9s %9s %9s %9s" % ("高度%", "z(mm比)", "宽1", "宽2", "顶点数"))
    rows = []
    for pct in range(0, 101, 4):
        z = hmin + total * pct / 100.0
        band = total * 0.012
        m = (h >= z - band) & (h <= z + band)
        sel = verts[m]
        if len(sel) < 3:
            print("%6d %9.3f      ---" % (pct, pct / 100 * total))
            continue
        w1 = sel[:, other[0]].max() - sel[:, other[0]].min()
        w2 = sel[:, other[1]].max() - sel[:, other[1]].min()
        rows.append((pct, w1, w2, len(sel)))
        print("%6d %9.3f %9.4f %9.4f %9d" % (pct, pct / 100 * total, w1, w2, len(sel)))

    # 用宽度突变找关键分界：头发/头 -> 颈 处宽度骤减
    print("\n=== 宽度变化率（找脖子/肩/腰）===")
    prev = None
    for pct, w1, w2, _ in rows:
        w = max(w1, w2)
        if prev is not None:
            print("%6d  宽度 %.4f  变化 %+.1f%%" % (pct, w, (w - prev) / prev * 100 if prev else 0))
        prev = w


if __name__ == "__main__":
    main(sys.argv[1])
