"""通用 md -> 单文件 HTML（深色主题，支持表格/代码，可离线看）。
用法: python md2html.py <src.md> <dst.html> <标题>
"""
import os
import re
import sys

import markdown

CSS = """
*{box-sizing:border-box}
body{margin:0;padding:0;background:#0f1115;color:#dfe3ea;
font:16px/1.75 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;}
.wrap{max-width:900px;margin:0 auto;padding:32px 20px 120px}
h1{font-size:27px;line-height:1.35;margin:.2em 0 .8em;color:#fff;letter-spacing:-.3px}
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
a{color:#8ab4ff}
.nav{position:sticky;top:0;background:rgba(15,17,21,.94);backdrop-filter:blur(8px);
border-bottom:1px solid #262b36;padding:10px 20px;font-size:13px;z-index:9;margin:-32px -20px 20px}
.nav a{display:inline-block;margin:3px 12px 3px 0;text-decoration:none;color:#8b95a7}
.nav a:hover{color:#8ab4ff}
@media print{body{background:#fff;color:#111}.nav{display:none}
h2{color:#000;border-color:#ccc}h3,h4{color:#000}th{background:#eee;color:#000}
td,th{border-color:#ccc}tr:nth-child(even) td{background:#fafafa}
blockquote{background:#fffbe6;border-color:#d4a017;color:#333}code{background:#f2f2f2;color:#0a6}}
"""

TPL = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>{css}</style></head>
<body><div class="nav">{nav}</div><div class="wrap">{body}</div></body></html>
"""


def build(src, dst, title):
    with open(src, encoding="utf-8") as f:
        md = f.read()
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "toc"])
    nav = "".join(
        '<a href="#%s">%s</a>' % (sid, re.sub(r"<[^>]+>", "", txt))
        for sid, txt in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    )
    html = TPL.format(title=title, css=CSS, nav=nav, body=body)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(html)
    print("written %s (%.0f KB)" % (dst, os.path.getsize(dst) / 1024))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "手册")
