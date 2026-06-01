#!/usr/bin/env python3
"""将考点版笔记转换为左右分栏的HTML复习页面（使用PDF.js渲染PDF）"""
import re
import markdown
import urllib.parse

# PDF 文件名
PDF_FILENAME = "动手学深度学习-PyTorch(第二版) (Aston Zhang, Zachary C. Lipton, 李沐 etc.) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
PDF_URL = urllib.parse.quote(PDF_FILENAME)

# 印刷页码 → PDF 页码偏移量
# （PDF前18页为封面/目录/前言等，正文从第19页开始对应印刷第1页）
PAGE_OFFSET = 18

# 读取 markdown 笔记
with open("复习笔记_考点版.md", "r", encoding="utf-8") as f:
    md_content = f.read()

# 去掉图片引用
md_content = re.sub(r'!\[.*?\]\(.*?\)', '', md_content)

# 将 md 转为 html
html_body = markdown.markdown(
    md_content,
    extensions=['tables', 'fenced_code', 'codehilite'],
    extension_configs={'codehilite': {'css_class': 'highlight'}}
)

# 给页码添加可点击链接（印刷页码 → PDF页码）
def add_page_links(text):
    def replace_page(m):
        num = int(m.group(1))
        pdf_num = num + PAGE_OFFSET
        return f'<a href="javascript:void(0)" onclick="jumpToPage({pdf_num})" class="page-link" title="教材第{num}页 → PDF第{pdf_num}页">p{num}</a>'
    return re.sub(r'p(\d+)(?!\d*["\'>])', replace_page, text)

html_body = add_page_links(html_body)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>深度学习期末复习</title>
<!-- PDF.js -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';</script>
<!-- KaTeX -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ height: 100%; overflow: hidden; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; }}

  .container {{ display: flex; height: 100vh; }}

  /* ===== 左侧 PDF 面板 ===== */
  .pdf-panel {{
    display: flex; flex-direction: column;
    background: #525659;
    min-width: 200px;
    width: calc(100% - 460px);
  }}
  .pdf-toolbar {{
    background: #323639; color: #fff;
    padding: 6px 16px;
    display: flex; align-items: center; gap: 12px;
    font-size: 13px; flex-shrink: 0;
  }}
  .pdf-toolbar input {{
    width: 60px; padding: 2px 6px; text-align: center;
    border: 1px solid #666; background: #1a1a1a; color: #fff; border-radius: 3px;
  }}
  .pdf-toolbar button,.pdf-toolbar select {{
    background: #555; color: #fff; border: none; padding: 3px 10px;
    border-radius: 3px; cursor: pointer; font-size: 12px;
  }}
  .pdf-toolbar button:hover,.pdf-toolbar select:hover {{ background: #777; }}
  .pdf-toolbar .total {{ color: #aaa; font-size: 12px; }}
  .pdf-toolbar .zoom-control {{ margin-left: auto; display: flex; align-items: center; gap: 4px; }}

  .pdf-viewport {{
    flex: 1; overflow: auto;
    background: #525659;
    position: relative;
  }}
  .pdf-viewport .pdf-wrapper {{
    text-align: center;
    padding: 10px;
    min-width: 100%;
  }}
  .pdf-viewport .pdf-page-container {{
    display: inline-block;
    position: relative;
  }}
  .pdf-viewport canvas {{
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
    background: #fff;
    display: block;
  }}
  /* PDF.js 文本层（支持选中/复制文字） */
  .textLayer {{
    position: absolute; left: 0; top: 0; right: 0; bottom: 0;
    line-height: 1.0;
    overflow: hidden;
    opacity: 0.25;
  }}
  .textLayer span, .textLayer br {{
    color: transparent;
    position: absolute;
    white-space: pre;
    cursor: text;
    transform-origin: 0% 0%;
  }}
  .textLayer ::selection {{ background: rgba(60,132,244,0.4); color: transparent; }}
  .textLayer ::-moz-selection {{ background: rgba(60,132,244,0.4); color: transparent; }}
  .textLayer span.hl {{ background: rgba(255,255,0,0.5); border-radius: 2px; }}
  .pdf-loading {{
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    color: #fff; text-align: center;
  }}
  .pdf-loading .spinner {{
    border: 4px solid rgba(255,255,255,0.2);
    border-top: 4px solid #fff;
    border-radius: 50%;
    width: 40px; height: 40px;
    animation: spin 1s linear infinite;
    margin: 0 auto 16px;
  }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  .pdf-error {{
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    color: #fff; text-align: center;
    background: rgba(0,0,0,0.8);
    padding: 30px; border-radius: 8px;
    max-width: 400px;
  }}
  .pdf-error code {{ background: #444; padding: 2px 6px; border-radius: 3px; font-size: 13px; }}

  /* ===== 拖拽分隔条 ===== */
  .divider {{
    width: 6px; background: #ccc; cursor: col-resize;
    flex-shrink: 0; position: relative; z-index: 10;
    transition: background 0.15s;
  }}
  .divider:hover, .divider.active {{ background: #3498db; }}
  .divider::after {{
    content: '⋮'; position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%); color: #999; font-size: 14px;
  }}
  .divider:hover::after, .divider.active::after {{ color: #fff; }}

  /* ===== 右侧笔记面板 ===== */
  .note-panel {{
    display: flex; flex-direction: column;
    background: #fafafa;
    min-width: 300px; width: 460px;
  }}
  .note-header {{
    background: #2c3e50; color: #fff;
    padding: 10px 16px; font-size: 14px; font-weight: bold;
    flex-shrink: 0; display: flex; justify-content: space-between; align-items: center;
  }}
  .note-header input {{
    padding: 3px 8px; border: 1px solid #555; border-radius: 3px;
    background: #1a1a1a; color: #fff; width: 150px; font-size: 12px;
  }}
  .note-header button {{
    background: #3498db; color: #fff; border: none;
    padding: 3px 10px; border-radius: 3px; cursor: pointer; font-size: 12px;
  }}
  .note-header button:hover {{ background: #2980b9; }}

  .note-content {{
    flex: 1; overflow-y: auto;
    padding: 16px 20px; font-size: 14px; line-height: 1.7; color: #333;
  }}

  /* 笔记内容样式 */
  .note-content h1 {{ font-size: 22px; margin: 0 0 10px; color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 6px; }}
  .note-content h2 {{ font-size: 18px; margin: 20px 0 10px; color: #e74c3c; border-bottom: 1px solid #e74c3c; padding-bottom: 4px; }}
  .note-content h3 {{ font-size: 16px; margin: 16px 0 8px; color: #2980b9; background: #eaf2f8; padding: 4px 10px; border-radius: 4px; }}
  .note-content table {{
    border-collapse: collapse; width: 100%; margin: 8px 0;
    font-size: 13px; border: 1px solid #ddd;
  }}
  .note-content th, .note-content td {{ border: 1px solid #ddd; padding: 6px 10px; vertical-align: top; }}
  .note-content th {{ background: #34495e; color: #fff; white-space: nowrap; width: 90px; }}
  .note-content tr:nth-child(even) {{ background: #f8f9fa; }}
  .note-content blockquote {{
    border-left: 4px solid #2c3e50; margin: 8px 0; padding: 6px 12px;
    background: #f0f4f8; color: #555; font-size: 13px;
  }}
  .note-content code {{
    background: #f0f0f0; padding: 1px 5px; border-radius: 3px;
    font-size: 13px; color: #c0392b; font-family: 'Consolas', monospace;
  }}
  .note-content strong {{ color: #2c3e50; }}

  a.page-link {{
    display: inline-block; background: #3498db; color: #fff !important;
    padding: 0 5px; border-radius: 3px; text-decoration: none;
    font-weight: bold; font-size: 12px; cursor: pointer;
    transition: background 0.2s;
  }}
  a.page-link:hover {{ background: #e74c3c; }}

  .highlight-match {{ background: #ffff99; padding: 0 2px; }}

  @media (max-width: 900px) {{
    .container {{ flex-direction: column; }}
    .pdf-panel {{ height: 50vh; width: 100% !important; flex: none !important; }}
    .note-panel {{ width: 100% !important; height: 50vh; flex: none !important; }}
    .divider {{ display: none; }}
  }}
</style>
</head>
<body>

<div class="container">
  <!-- 左侧 PDF -->
  <div class="pdf-panel">
    <div class="pdf-toolbar">
      <span>📄</span>
      <button onclick="prevPage()" title="上一页">◀</button>
      <span>第 <input type="text" id="pageInput" value="-" style="width:50px" onkeyup="if(event.key==='Enter')jumpToPage(parseInt(this.value))"> 页</span>
      <span class="total" id="totalPages"></span>
      <button onclick="nextPage()" title="下一页">▶</button>
      <span class="zoom-control">
        <button onclick="zoomOut()">−</button>
        <span id="zoomLevel" style="color:#aaa;min-width:40px;text-align:center">100%</span>
        <button onclick="zoomIn()">+</button>
      </span>
    </div>
    <div class="pdf-viewport" id="pdfViewport">
      <div class="pdf-loading" id="pdfLoading">
        <div class="spinner"></div>
        <div>正在加载 PDF...</div>
      </div>
      <div class="pdf-wrapper">
        <div class="pdf-page-container">
          <canvas id="pdfCanvas"></canvas>
          <div class="textLayer" id="textLayer"></div>
        </div>
      </div>
      <div class="pdf-error" id="pdfError" style="display:none">
        <div style="font-size:36px;margin-bottom:10px">⚠️</div>
        <div style="font-size:16px;margin-bottom:8px">PDF 加载失败</div>
        <div style="font-size:13px;color:#aaa;margin-bottom:12px">
          浏览器安全策略限制了本地文件访问。<br><br>
          请用以下任一方式：<br><br>
          <b>方式一（推荐）：</b><br>
          在终端运行：<br>
          <code>python3 -m http.server 8080</code><br>
          然后访问 <code>http://localhost:8080/复习笔记_考点版.html</code><br><br>
          <b>方式二：</b><br>
          使用 Firefox 浏览器打开此页面
        </div>
        <button onclick="location.reload()" style="padding:8px 20px;background:#3498db;color:#fff;border:none;border-radius:4px;cursor:pointer">重新加载</button>
      </div>
    </div>
  </div>

  <!-- 拖拽分隔条 -->
  <div class="divider" id="divider"></div>

  <!-- 右侧笔记 -->
  <div class="note-panel">
    <div class="note-header">
      <span>📝 考点笔记</span>
      <div>
        <input type="text" id="searchInput" placeholder="搜索..." style="width:120px" onkeyup="if(event.key==='Enter')doSearch()">
        <button onclick="clearSearch()">✕</button>
      </div>
    </div>
    <div class="note-content" id="noteContent">
{html_body}
    </div>
  </div>
</div>

<script>
// ===== PDF.js =====
var pdfDoc = null, pageNum = 1, scale = 1.2, pageRendering = false;
var highlights = {{}}; // {{pageNum: [spanIndex, ...]}} 高亮标记
var currentTextDivs = []; // renderTextLayer 创建的文本 span 数组

var canvas = document.getElementById('pdfCanvas');
var ctx = canvas.getContext('2d');

function loadPDF() {{
    var url = '{PDF_URL}';
    pdfjsLib.getDocument(url).promise.then(function(doc) {{
        pdfDoc = doc;
        document.getElementById('totalPages').textContent = '/ ' + doc.numPages + ' 页';
        document.getElementById('pdfLoading').style.display = 'none';
        renderPage(pageNum);
    }}).catch(function(err) {{
        console.error('PDF load error:', err);
        document.getElementById('pdfLoading').style.display = 'none';
        document.getElementById('pdfError').style.display = 'block';
    }});
}}

function renderPage(num) {{
    if (pageRendering || !pdfDoc) return;
    pageRendering = true;

    // 清除旧文本层及 textDivs 引用
    var textLayerDiv = document.getElementById('textLayer');
    textLayerDiv.innerHTML = '';
    currentTextDivs = [];

    pdfDoc.getPage(num).then(function(page) {{
        var viewport = page.getViewport({{ scale: scale }});
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        canvas.style.width = viewport.width + 'px';
        canvas.style.height = viewport.height + 'px';

        var renderContext = {{
            canvasContext: ctx,
            viewport: viewport
        }};

        // 先渲染 canvas
        return page.render(renderContext).promise.then(function() {{
            // 再渲染文本层（支持选中/复制文字）
            return page.getTextContent().then(function(textContent) {{
                textLayerDiv.style.width = viewport.width + 'px';
                textLayerDiv.style.height = viewport.height + 'px';
                textLayerDiv.style.setProperty('--scale-factor', viewport.scale);
                var task = pdfjsLib.renderTextLayer({{
                    textContentSource: textContent,
                    container: textLayerDiv,
                    viewport: viewport,
                    textDivs: currentTextDivs,
                    enhanceTextSelection: false
                }});
                if (task && task.promise) return task.promise;
            }});
        }});
    }}).then(function() {{
        pageRendering = false;
        pageNum = num;
        document.getElementById('pageInput').value = num;
        document.getElementById('pdfViewport').scrollTop = 0;
        // textDivs 已就绪，恢复高亮
        restoreHighlights(num);
    }}).catch(function(err) {{
        pageRendering = false;
        console.error('Render error:', err);
    }});
}}

// ===== 高亮标记功能 =====
function restoreHighlights(num) {{
    if (!highlights[num]) return;
    highlights[num].forEach(function(idx) {{
        if (idx < currentTextDivs.length) {{
            currentTextDivs[idx].classList.add('hl');
        }}
    }});
}}

document.addEventListener('contextmenu', function(e) {{
    // 只处理 textLayer 内的右键
    if (!e.target.closest('#textLayer')) return;
    var sel = window.getSelection();
    if (!sel.isCollapsed && sel.rangeCount > 0) {{
        e.preventDefault();
        var range = sel.getRangeAt(0);
        var indices = [];
        currentTextDivs.forEach(function(div, idx) {{
            if (range.intersectsNode(div)) indices.push(idx);
        }});
        if (indices.length > 0) {{
            if (!highlights[pageNum]) highlights[pageNum] = [];
            indices.forEach(function(idx) {{
                if (highlights[pageNum].indexOf(idx) === -1) {{
                    highlights[pageNum].push(idx);
                    currentTextDivs[idx].classList.add('hl');
                }}
            }});
        }}
        sel.removeAllRanges();
    }}
}});

function jumpToPage(num) {{
    num = parseInt(num);
    if (isNaN(num) || !pdfDoc) return;
    num = Math.max(1, Math.min(num, pdfDoc.numPages));
    renderPage(num);
}}

function prevPage() {{ jumpToPage(pageNum - 1); }}
function nextPage() {{ jumpToPage(pageNum + 1); }}

function zoomIn() {{ scale = Math.min(scale + 0.1, 3.0); updateZoom(); }}
function zoomOut() {{ scale = Math.max(scale - 0.1, 0.4); updateZoom(); }}
function updateZoom() {{
    document.getElementById('zoomLevel').textContent = Math.round(scale * 100) + '%';
    if (pdfDoc) renderPage(pageNum);
}}

// 键盘快捷键
document.addEventListener('keydown', function(e) {{
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'ArrowLeft') {{ e.preventDefault(); prevPage(); }}
    if (e.key === 'ArrowRight') {{ e.preventDefault(); nextPage(); }}
    if (e.key === '+' || e.key === '=') {{ e.preventDefault(); zoomIn(); }}
    if (e.key === '-') {{ e.preventDefault(); zoomOut(); }}
}});

// 鼠标滚轮缩放（Ctrl+滚轮）
document.getElementById('pdfViewport').addEventListener('wheel', function(e) {{
    if (e.ctrlKey) {{ e.preventDefault(); if (e.deltaY < 0) zoomIn(); else zoomOut(); }}
}}, {{ passive: false }});

// ===== 搜索功能 =====
function doSearch() {{
    var query = document.getElementById('searchInput').value.trim().toLowerCase();
    var content = document.getElementById('noteContent');
    // 清除旧高亮
    content.innerHTML = content.innerHTML.replace(/<span class="highlight-match">(.*?)<\\/span>/g, '$1');
    if (!query) return;

    var walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, null, false);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach(function(node) {{
        if (node.parentNode && node.parentNode.classList.contains('highlight-match')) return;
        var text = node.textContent.toLowerCase();
        var idx = text.indexOf(query);
        if (idx >= 0) {{
            var span = document.createElement('span');
            span.appendChild(document.createTextNode(node.textContent.substring(0, idx)));
            var mark = document.createElement('span');
            mark.className = 'highlight-match';
            mark.textContent = node.textContent.substring(idx, idx + query.length);
            span.appendChild(mark);
            var after = node.textContent.substring(idx + query.length);
            if (after) span.appendChild(document.createTextNode(after));
            node.parentNode.replaceChild(span, node);
        }}
    }});
}}

function clearSearch() {{
    document.getElementById('searchInput').value = '';
    var c = document.getElementById('noteContent');
    c.innerHTML = c.innerHTML.replace(/<span class="highlight-match">(.*?)<\\/span>/g, '$1');
}}

// ===== 拖拽分隔条 =====
(function() {{
    var divider = document.getElementById('divider');
    var container = document.querySelector('.container');
    var pdfPanel = document.querySelector('.pdf-panel');
    var notePanel = document.querySelector('.note-panel');
    var isDragging = false;

    divider.addEventListener('mousedown', function() {{
        isDragging = true;
        divider.classList.add('active');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    }});

    document.addEventListener('mousemove', function(e) {{
        if (!isDragging) return;
        var rect = container.getBoundingClientRect();
        var offset = e.clientX - rect.left;
        var dw = 6, minL = 200, minR = 300;
        var leftW = Math.max(minL, Math.min(offset, rect.width - minR - dw));
        var rightW = rect.width - leftW - dw;
        if (rightW < minR) {{ rightW = minR; leftW = rect.width - rightW - dw; }}
        pdfPanel.style.width = leftW + 'px';
        pdfPanel.style.flex = 'none';
        notePanel.style.width = rightW + 'px';
        notePanel.style.flex = 'none';
    }});

    document.addEventListener('mouseup', function() {{
        if (isDragging) {{
            isDragging = false;
            divider.classList.remove('active');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }}
    }});
}})();

// ===== 渲染 KaTeX =====
try {{ renderMathInElement(document.getElementById('noteContent'), {{
    delimiters: [{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}],
    throwOnError: false
}}); }} catch(e) {{}}

// ===== 启动加载 PDF =====
loadPDF();
</script>

</body>
</html>
"""

with open("复习笔记_考点版.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ 已生成: 复习笔记_考点版.html")
print()
print("⚠️ 由于浏览器安全策略，直接双击打开可能无法加载 PDF。")
print("   请在终端运行以下命令后访问：")
print()
print("   cd", PDF_FILENAME.rsplit("/", 1)[0] if "/" in PDF_FILENAME else "当前目录")
print("   python3 -m http.server 8080")
print()
print("   然后浏览器打开: http://localhost:8080/复习笔记_考点版.html")
print()
print("   或用 Firefox 浏览器直接打开此 HTML 文件")
print()
print("   功能：← → 翻页  |  Ctrl+滚轮 缩放  |  搜索考点  |  拖拽调整面板")
