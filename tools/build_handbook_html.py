"""把手册 md 转成单文件 HTML（内嵌对比图，可离线手机看）。"""
import base64
import io
import re

import markdown

SRC = "blender-figure-tuneup-handbook.md"
DST = "blender-figure-tuneup-handbook.html"
IMG = "tmp_3dgen/compare.jpg"

with open(IMG, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

with open(SRC, encoding="utf-8") as f:
    md = f.read()

body = markdown.markdown(md, extensions=["tables", "fenced_code", "toc"])

# 插入对比图到第 1 章标题后
img_html = (
    '<figure class="cmp">'
    '<img src="data:image/jpeg;base64,%s" alt="照片与模型对比">'
    '<figcaption>左：原照片（正面站）。右：v2 模型预览——<b>这是渲染相机放在 45° 斜侧方的结果，'
    '不是模型姿势错了</b>。四向正交验证确认：身体正对、脸朝前，只有头转了 15-20°。</figcaption>'
    '</figure>' % b64
)
anchor = "我提前诊断出的模型问题"
idx = body.find(anchor)
if idx > 0:
    end = body.find("</h2>", idx) + 5
    body = body[:end] + img_html + body[end:]
else:
    print("WARN: 未找到插入锚点，图片未插入")

tpl = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>回家动手单 · Blender 改像手办模型</title>
<style>
*{box-sizing:border-box}
body{margin:0;padding:0;background:#0f1115;color:#dfe3ea;
font:16px/1.75 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;}
.wrap{max-width:900px;margin:0 auto;padding:32px 20px 120px}
h1{font-size:28px;line-height:1.35;margin:.2em 0 .8em;color:#fff;letter-spacing:-.3px}
h2{font-size:21px;margin:2.2em 0 .7em;padding-bottom:.35em;border-bottom:1px solid #262b36;color:#8ab4ff}
h3{font-size:17px;margin:1.6em 0 .5em;color:#ffd479}
h4{font-size:15px;margin:1.2em 0 .4em;color:#9fe3b0}
p{margin:.7em 0}
ul,ol{padding-left:1.4em;margin:.6em 0}
li{margin:.3em 0}
strong{color:#fff}
code{background:#1b2029;border:1px solid #2a3040;border-radius:4px;padding:1px 5px;
font:13px/1.4 ui-monospace,Consolas,monospace;color:#9fe3b0;word-break:break-all}
pre{background:#151a22;border:1px solid #2a3040;border-radius:8px;padding:14px 16px;overflow-x:auto}
pre code{background:none;border:none;padding:0;color:#c8d3e0}
table{width:100%;border-collapse:collapse;margin:1em 0;font-size:14px;display:block;overflow-x:auto}
th,td{border:1px solid #2a3040;padding:8px 10px;text-align:left;vertical-align:top}
th{background:#1b2029;color:#8ab4ff;font-weight:600;white-space:nowrap}
tr:nth-child(even) td{background:#131820}
blockquote{margin:1em 0;padding:.6em 1em;border-left:3px solid #ffd479;background:#1a1708;color:#e8dcb8;border-radius:0 6px 6px 0}
blockquote p{margin:.25em 0}
hr{border:none;border-top:1px solid #262b36;margin:2.4em 0}
.cmp{margin:1.4em 0;padding:12px;background:#151a22;border:1px solid #2a3040;border-radius:10px}
.cmp img{width:100%;display:block;border-radius:6px}
.cmp figcaption{font-size:13px;color:#8b95a7;margin-top:10px;line-height:1.6}
a{color:#8ab4ff}
.nav{position:sticky;top:0;background:rgba(15,17,21,.94);backdrop-filter:blur(8px);
border-bottom:1px solid #262b36;padding:10px 20px;font-size:13px;z-index:9;margin:-32px -20px 20px}
.nav a{display:inline-block;margin:3px 12px 3px 0;text-decoration:none;color:#8b95a7}
.nav a:hover{color:#8ab4ff}
@media print{body{background:#fff;color:#111}.nav{display:none}
h2{color:#000;border-color:#ccc}h3,h4{color:#000}th{background:#eee;color:#000}
td,th{border-color:#ccc}tr:nth-child(even) td{background:#fafafa}
blockquote{background:#fffbe6;border-color:#d4a017;color:#333}code{background:#f2f2f2;color:#0a6}}
</style>
</head>
<body>
<div class="nav">
<a href="#0-开工前必须知道的三件事">0 先读这个</a>
<a href="#1-我提前诊断出的模型问题">1 模型诊断</a>
<a href="#2-装环境15-分钟">2 装环境</a>
<a href="#3-导入--第一步必做10-分钟">3 导入</a>
<a href="#4-必会的-9-个操作练-20-分钟够用全程">4 快捷键</a>
<a href="#5-施工顺序按序做别跳">5 施工</a>
<a href="#6-体检与导出20-分钟">6 导出</a>
<a href="#7-交付厂商怎么说关键">7 交付</a>
<a href="#8-卡住了怎么办兜底四条">8 兜底</a>
</div>
<div class="wrap">
__BODY__
</div>
</body>
</html>
"""

html = tpl.replace("__BODY__", body)
with open(DST, "w", encoding="utf-8") as f:
    f.write(html)
print("written %s  (%.0f KB)" % (DST, len(html.encode()) / 1024))
