"""Blender 辅助脚本 —— 手办打印前处理
在 Blender 里：Scripting 工作区 → Open 选本文件 → ▶ Run Script
若报错看不到信息：Window → Toggle System Console

做三件事：
  1) 把选中的模型等比缩放到目标高度（默认 150mm）并应用缩放
  2) 可选：自动加一个底座
  3) 打印水密性 / 尺寸 / 面数体检报告

只改尺寸和加底座，不动几何形状 —— 形状你自己用雕刻改。
"""

import os

import bpy
import bmesh
from mathutils import Vector  # noqa: F401

# ============ 参数区（要改就改这里）============
TARGET_HEIGHT_MM = 150.0   # 成品高度，毫米
DO_SCALE = True            # 是否自动缩放
DO_BASE = False            # 是否自动加底座（建议先改形状，最后再开这个）
BASE_DIAMETER_MM = 65.0    # 底座直径
BASE_THICK_MM = 4.0        # 底座厚度
BASE_EMBED_MM = 0.5        # 底座顶面嵌入脚底的深度（防悬空）
# ==============================================

report = []


def log(msg):
    report.append(str(msg))
    print(msg)


def flush_report():
    """把报告写到脚本同目录，方便复制粘贴给技术支持。"""
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals()
                            else bpy.app.tempdir, "figure_report.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        log("\n[报告已写出] %s" % path)
    except Exception as e:  # noqa: BLE001
        log("(报告写文件失败：%s)" % e)


def get_mesh_object():
    obj = bpy.context.active_object
    if obj is None or obj.type != "MESH":
        # 退化：场景里只有一个 mesh 就用它
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        if len(meshes) == 1:
            obj = meshes[0]
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            log("提示：自动选中了场景里唯一的网格「%s」" % obj.name)
        else:
            return None
    return obj


def ensure_object_mode():
    try:
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:  # noqa: BLE001
        pass


def world_dimensions(obj):
    """返回世界坐标下的尺寸（考虑 scale 与 rotation 后的包围盒）。"""
    bpy.context.view_layer.update()
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return hi - lo, lo, hi


def scale_to_height(obj, target_mm):
    dim, _, _ = world_dimensions(obj)
    cur = max(dim.x, dim.y, dim.z)
    if cur <= 1e-6:
        log("模型尺寸为 0，跳过缩放")
        return False
    if abs(cur - target_mm) < 0.5:
        log("尺寸已经是 %.2f，无需缩放" % cur)
        return True
    factor = target_mm / cur
    log("当前最大尺寸 %.3f → 目标 %.1f，缩放系数 %.4f" % (cur, target_mm, factor))
    obj.scale = tuple(s * factor for s in obj.scale)
    ensure_object_mode()
    try:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        log("已应用缩放（scale 归 1）")
    except Exception as e:  # noqa: BLE001
        log("⚠️ 应用缩放失败：%s —— 请手动 Ctrl+A → Scale" % e)
    dim, _, _ = world_dimensions(obj)
    log("缩放后尺寸 X=%.2f Y=%.2f Z=%.2f" % (dim.x, dim.y, dim.z))
    return True


def check_mesh(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()

    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    loose = sum(1 for v in bm.verts if not v.link_edges)
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-9)

    # 连通块数量（判断是不是一堆散件）
    seen = set()
    islands = 0
    for v in bm.verts:
        if v.index in seen:
            continue
        islands += 1
        stack = [v]
        seen.add(v.index)
        while stack:
            cur = stack.pop()
            for e in cur.link_edges:
                other = e.other_vert(cur)
                if other.index not in seen:
                    seen.add(other.index)
                    stack.append(other)

    log("\n===== 网格体检 =====")
    log("面数        %d" % len(bm.faces))
    log("顶点数      %d" % len(bm.verts))
    log("非流形边    %d  %s" % (non_manifold, "✅" if non_manifold == 0 else "❌ 有洞或重叠面"))
    log("边界边      %d  %s" % (boundary, "✅" if boundary == 0 else "❌ 有开口"))
    log("孤立顶点    %d  %s" % (loose, "✅" if loose == 0 else "⚠️ 可清理"))
    log("零面积面    %d  %s" % (degenerate, "✅" if degenerate == 0 else "⚠️ 可清理"))
    log("独立件数量  %d  %s" % (islands, "✅ 单件" if islands == 1 else "⚠️ 多件（切片器一般能处理，但注意别悬空）"))
    bm.free()

    if non_manifold or boundary:
        log("\n修复建议：编辑模式全选 → Shift+N 重算法线 → 再 Check；仍有洞就 Mesh → Clean Up → Fill Holes")


def add_base(obj):
    ensure_object_mode()
    dim, lo, hi = world_dimensions(obj)

    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=BASE_DIAMETER_MM / 2.0,
        depth=BASE_THICK_MM,
        location=((lo.x + hi.x) / 2.0, (lo.y + hi.y) / 2.0,
                  lo.z - BASE_THICK_MM / 2.0 + BASE_EMBED_MM),
    )
    base = bpy.context.active_object
    base.name = "figure_base"
    log("\n底座：直径 %.0fmm 厚 %.0fmm，顶面嵌入脚底 %.1fmm" % (BASE_DIAMETER_MM, BASE_THICK_MM, BASE_EMBED_MM))
    log("⚠️ 底座和模型还没合并。想合并：同时选中两者 → Ctrl+J（合并前建议先 Ctrl+S 存盘）")

    # 底座是否够宽：检查模型 XY 投影是否超出
    if dim.x > BASE_DIAMETER_MM or dim.y > BASE_DIAMETER_MM:
        log("⚠️ 模型 XY 投影 (%.1f×%.1f) 大于底座直径 %.1f，手/包可能悬空 —— 建议把 BASE_DIAMETER_MM 调大"
            % (dim.x, dim.y, BASE_DIAMETER_MM))
    return base


def main():
    log("========== 手办打印前处理 ==========")
    obj = get_mesh_object()
    if obj is None:
        log("❌ 没有选中网格物体。请先在 3D 视图里点一下模型，再重新运行脚本。")
        flush_report()
        return

    log("目标物体：%s" % obj.name)
    dim, lo, hi = world_dimensions(obj)
    log("原始尺寸 X=%.3f Y=%.3f Z=%.3f" % (dim.x, dim.y, dim.z))
    log("最低点 Z=%.3f（脚底）" % lo.z)

    if DO_SCALE:
        scale_to_height(obj, TARGET_HEIGHT_MM)

    check_mesh(obj)

    if DO_BASE:
        add_base(obj)
    else:
        log("\n(未加底座。需要时把顶部 DO_BASE 改成 True 再跑一次)")

    log("\n===== 接下来 =====")
    log("1. Ctrl+S 存 .blend")
    log("2. File → Export → STL（Binary / Selection Only / Scale=1.0）")
    log("3. 用 Windows 3D 查看器打开 STL，确认高度约 %.0f mm" % TARGET_HEIGHT_MM)
    flush_report()


main()
