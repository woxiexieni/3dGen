"""打包回家用的资料包（ASCII 文件名，解压即用）。"""
import os
import zipfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "3dGen-homework-kit.zip")

FILES = [
    ("3d_model/girlfriend_standing.glb", "girlfriend_standing.glb"),
    ("tmp_3dgen/input_resized_v2.jpg", "input_resized_v2.jpg"),
    ("blender-figure-tuneup-handbook.html", "handbook.html"),
    ("blender-figure-tuneup-handbook.md", "handbook.md"),
    ("tools/blender_figure_helper.py", "blender_figure_helper.py"),
]

README = """回家开工说明
================

一、先装 Blender
  https://www.blender.org/download/   下 LTS 版，Windows Installer
  装完做 4 个设置（Edit > Preferences）：
    Input      -> 勾 Emulate Numpad（笔记本没小键盘必开）
    Add-ons    -> 搜 3D-Print -> 勾 Mesh: 3D-Print Toolbox
    Save&Load  -> 勾 Auto Save Temporary Files
    （单位不用设，手册第 3 章统一处理）

二、解压后打开 handbook.html（双击即可，图片已内嵌，断网也能看）
  按 0 章 -> 3 章 -> 5 章的 S1 一路做下去。

三、顺序只有一条不能错：
  S 输入 150/1.1644  ->  Ctrl+A -> Scale
  不做这步，导出的 STL 在切片器里只有 0.15mm，全是废的。

四、核心判断（省你三小时）：
  1. 别修脸。15cm 手办的脸只有 15mm 宽，五官印不出来，靠后期涂装。
  2. 头发改对，人就有一半像了。
  3. 头掰正，正脸朝前。
  4. 交付走「光固化素模 + 找人代涂」，比全彩打印像得多。

五、blender_figure_helper.py 怎么用：
  Blender 顶部切到 Scripting 工作区 -> Open 选它 -> 点右上角播放键
  它做三件事：定尺寸到 150mm / 加底座 / 水密体检
  默认不加底座；要加就把文件顶部 DO_BASE 改成 True

六、导出 STL 后一定要验：
  用 Windows 自带的「3D 查看器」打开，显示高度约 150mm 才对。

有问题随时回来找我。
"""

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for src, arc in FILES:
        p = os.path.join(BASE, src)
        if not os.path.exists(p):
            print("MISSING", src)
            continue
        z.write(p, "3dGen-homework-kit/" + arc)
        print("add %-40s %6.1f MB" % (arc, os.path.getsize(p) / 1048576))
    z.writestr("3dGen-homework-kit/README.txt", README)

print("\n-> %s  (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1048576))
