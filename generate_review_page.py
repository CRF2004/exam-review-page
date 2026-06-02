#!/usr/bin/env python3
"""将考点版笔记转换为左右分栏的HTML复习页面（支持多PDF + 跨文件页码跳转）

用法:
  python3 generate_review_page.py                   # 使用预设 PDF_FILES 配置
  python3 generate_review_page.py --scan             # 自动扫描当前目录 PDF 并输出配置模板
"""
import re
import json
import sys
import os
import glob
import markdown
import urllib.parse

# ============================================================
# 多 PDF 配置（手动编辑）
# ============================================================
# 标识：笔记中引用时使用的短名称，如 `讲义一 p42`
# file：PDF 文件名（与脚本同目录）
# offset：印刷页码 → PDF 页码的差值
# label：左侧工具栏下拉框中显示的名称

PDF_FILES = {
    "default": {"file": "materials/course-material.pdf", "offset": 0, "label": "默认资料"},
    # 按实际课程材料编辑：
    #   key     — 笔记里引用时使用的标识，如 `讲义二 p42`
    #   file    — PDF 文件相对路径
    #   offset  — 印刷页码 → PDF 页码偏移量（建议优先保持 0）
    #   label   — 页面下拉框显示名称
}

# 默认打开的 PDF 标识（必须是 PDF_FILES 中的某个 key）
DEFAULT_PDF_KEY = "default"

# 输入/输出文件名
INPUT_MD = "复习笔记_考点版.md"
OUTPUT_HTML = "复习笔记_考点版.html"
PAGE_TITLE = "复习笔记"
PAGE_LAYOUT = "split"

# ============================================================
# PDF 自动扫描工具
# ============================================================

def auto_scan_pdfs(directory="."):
    """扫描目录中的 PDF，尝试根据文件名自动生成配置。"""
    CHINESE_NUMS = "一二三四五六七八九十"
    pdfs = {}
    files = sorted(glob.glob(os.path.join(directory, "*.pdf")))
    for f in files:
        basename = os.path.basename(f)
        name_no_ext = os.path.splitext(basename)[0]
        m = re.search(r'讲义[（(]?([' + CHINESE_NUMS + r']+)[）)]?', name_no_ext)
        if m:
            key = "讲义" + m.group(1)
            label = f"讲义{m.group(1)}"
        else:
            key = name_no_ext
            label = name_no_ext
        pdfs[key] = {"file": basename, "offset": 0, "label": label}
    return pdfs

def print_config_template(pdfs):
    print("# 扫描到的 PDF 文件配置（请复制到脚本的 PDF_FILES 中）：")
    print("PDF_FILES = {")
    for key, cfg in pdfs.items():
        print(f'    "{key}": {json.dumps(cfg, ensure_ascii=False)},')
    print("}")

# ============================================================
# 页码链接处理
# ============================================================

def add_page_links(text, pdf_files, default_key):
    """将笔记中的页码引用转为可点击的 PDF 跳转链接。

    - `p105`           → 跳转当前/默认 PDF 第 105 页
    - `讲义三 p42`     → 切换到"讲义三"并跳转第 42 页
    """
    valid_keys = sorted([k for k in pdf_files if k != default_key], key=len, reverse=True)
    chinese_keys = [k for k in valid_keys if re.fullmatch(r'[\u4e00-\u9fff]+', k)]

    # Pass 1: 跨文件链接 (讲义N p\d+ 或 讲义N p\d+-p\d+)
    if chinese_keys:
        key_pattern = "|".join(re.escape(k) for k in chinese_keys)
        cross_pattern = rf'({key_pattern})\s*p(\d+)(?:-p(\d+))?(?!\d*["\'>])'
        def replace_cross(m):
            key = m.group(1)
            start = int(m.group(2))
            cfg = pdf_files[key]
            start_pdf = start + cfg["offset"]
            result = (f'<a href="javascript:void(0)" '
                      f'onclick="jumpToPage(\'{key}\', {start_pdf})" '
                      f'class="page-link" '
                      f'title="{cfg["label"]} 第{start}页 → PDF 第{start_pdf}页">'
                      f'{key} p{start}</a>')
            end_str = m.group(3)
            if end_str:
                end = int(end_str)
                end_pdf = end + cfg["offset"]
                result += (f'-<a href="javascript:void(0)" '
                           f'onclick="jumpToPage(\'{key}\', {end_pdf})" '
                           f'class="page-link" '
                           f'title="{cfg["label"]} 第{end}页 → PDF 第{end_pdf}页">'
                           f'p{end}</a>')
            return result
        text = re.sub(cross_pattern, replace_cross, text)

    # Pass 2: 单文件链接 (p\d+)
    offset = pdf_files[default_key]["offset"]
    def replace_single(m):
        num = int(m.group(1))
        pdf_num = num + offset
        return (f'<a href="javascript:void(0)" '
                f'onclick="jumpToPage(\'{default_key}\', {pdf_num})" '
                f'class="page-link" '
                f'title="{pdf_files[default_key]["label"]} 第{num}页 → PDF 第{pdf_num}页">'
                f'p{num}</a>')
    text = re.sub(r'(?<![\u4e00-\u9fff])p(\d+)(?!\d*["\'<>])', replace_single, text)
    return text

# ============================================================
# HTML 模板
# ============================================================

def build_html(html_body, pdf_files, default_key, page_title):
    pdf_config_json = json.dumps(pdf_files, ensure_ascii=False)

    # 生成 PDF 选择器选项
    opts = []
    for key, cfg in pdf_files.items():
        sel = "selected" if key == default_key else ""
        opts.append(f'          <option value="{key}" {sel}>{cfg["label"]}</option>')
    selector_html = "\n".join(opts)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
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
    padding: 6px 12px;
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; flex-shrink: 0;
    flex-wrap: wrap;
  }}
  .pdf-toolbar input {{
    width: 50px; padding: 2px 6px; text-align: center;
    border: 1px solid #666; background: #1a1a1a; color: #fff; border-radius: 3px;
  }}
  .pdf-toolbar button,.pdf-toolbar select {{
    background: #555; color: #fff; border: none; padding: 3px 10px;
    border-radius: 3px; cursor: pointer; font-size: 12px;
  }}
  .pdf-toolbar button:hover,.pdf-toolbar select:hover {{ background: #777; }}
  .pdf-toolbar .total {{ color: #aaa; font-size: 12px; }}
  .pdf-toolbar .zoom-control {{ margin-left: auto; display: flex; align-items: center; gap: 4px; }}
  .pdf-file-select {{
    background: #444; color: #fff; border: none;
    padding: 3px 8px; border-radius: 3px; font-size: 12px;
    cursor: pointer; max-width: 180px;
  }}
  .pdf-file-select:hover {{ background: #666; }}
  .pdf-file-select option {{ background: #333; color: #fff; }}

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
  .textLayer ::selection {{ background: rgba(40, 110, 255, 0.55); color: transparent; }}
  .textLayer ::-moz-selection {{ background: rgba(40, 110, 255, 0.55); color: transparent; }}
  .highlightLayer {{ position: absolute; left: 0; top: 0; right: 0; bottom: 0; pointer-events: none; z-index: 2; }}
  .hl-rect {{ position: absolute; background: rgba(255, 190, 0, 0.55); border-radius: 2px; }}
  .annotationLayer {{
    position: absolute; left: 0; top: 0; right: 0; bottom: 0;
    z-index: 3; pointer-events: none;
  }}
  .text-note {{
    position: absolute;
    min-width: 120px;
    min-height: 72px;
    border: 1px solid rgba(245, 166, 35, 0.95);
    border-radius: 8px;
    background: rgba(255, 248, 196, 0.96);
    box-shadow: 0 8px 24px rgba(0,0,0,0.18);
    overflow: hidden;
    pointer-events: auto;
  }}
  .text-note.selected {{
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.35), 0 10px 26px rgba(0,0,0,0.22);
  }}
  .text-note-header {{
    height: 28px;
    padding: 0 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(245, 166, 35, 0.92);
    color: #4a3a00;
    font-size: 12px;
    font-weight: bold;
    cursor: move;
    user-select: none;
  }}
  .text-note-delete {{
    background: transparent;
    border: none;
    color: #4a3a00;
    font-size: 16px;
    line-height: 1;
    cursor: pointer;
    padding: 0 2px;
  }}
  .text-note-body {{
    width: 100%;
    height: calc(100% - 28px);
    border: none;
    outline: none;
    resize: none;
    padding: 8px 10px;
    font-size: 13px;
    line-height: 1.5;
    color: #333;
    background: transparent;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  }}
  .text-note-resizer {{
    position: absolute;
    width: 12px;
    height: 12px;
    right: 2px;
    bottom: 2px;
    cursor: nwse-resize;
    background:
      linear-gradient(135deg, transparent 0 42%, rgba(74,58,0,0.65) 42% 54%, transparent 54% 66%, rgba(74,58,0,0.65) 66% 78%, transparent 78%);
  }}
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
    background: #1a1a1a; color: #fff; width: 120px; font-size: 12px;
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
  <!-- 左侧 PDF 面板 -->
  <div class="pdf-panel">
    <div class="pdf-toolbar">
      <span>📄</span>
      <select class="pdf-file-select" id="pdfSelector" onchange="switchPDF(this.value)">
{selector_html}
      </select>
      <button onclick="prevPage()" title="上一页 (←)">◀</button>
      <span>第 <input type="text" id="pageInput" value="-" style="width:50px"
          onkeyup="if(event.key==='Enter'){{var v=parseInt(this.value);if(!isNaN(v))jumpToPage(null,v)}}"> 页</span>
      <span class="total" id="totalPages"></span>
      <button onclick="nextPage()" title="下一页 (→)">▶</button>
      <span class="zoom-control">
        <button onclick="insertTextNote()" title="在当前页插入文本框">＋笔记框</button>
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
        <div class="pdf-page-container" id="pdfPageContainer">
          <canvas id="pdfCanvas"></canvas>
          <div class="textLayer" id="textLayer"></div>
          <div class="highlightLayer" id="highlightLayer"></div>
          <div class="annotationLayer" id="annotationLayer"></div>
        </div>
      </div>
      <div class="pdf-error" id="pdfError" style="display:none">
        <div style="font-size:36px;margin-bottom:10px">⚠️</div>
        <div style="font-size:16px;margin-bottom:8px">PDF 加载失败</div>
        <div style="font-size:13px;color:#aaa;margin-bottom:12px">
          浏览器安全策略限制了本地文件访问或文件不存在。<br><br>
          请用以下任一方式：<br><br>
          <b>方式一（推荐）：</b><br>
          在终端运行：<br>
          <code>python3 -m http.server 8080</code><br>
          然后访问 <code>http://localhost:8080/{OUTPUT_HTML}</code><br><br>
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
      <span>📝 {page_title}</span>
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
// ===== 多 PDF 配置（由 Python 脚本生成）=====
var PDF_CONFIG = {pdf_config_json};
var DEFAULT_KEY = '{default_key}';

// ===== 状态 =====
var pdfDoc = null, pageNum = 1, scale = 1.2, pageRendering = false;
var highlights = {{}}; // {{pageNum: [{{id, scale, rects: [{{left,top,width,height}},...]}},...]}}
var textNotes = {{}}; // {{pageNum: [{{id,left,top,width,height,text}}]}}; 均为相对页面宽高的比例
var currentScale = 1.0;
var currentFile = DEFAULT_KEY;
var fileStates = {{}}; // {{fileKey: {{pageNum: N, highlights: H, textNotes: T }}}}
var pdfDocs = {{}}; // {{fileKey: pdfDoc}} — 已加载PDF文档缓存
var currentPageWidth = 0, currentPageHeight = 0;
var activeNoteId = null;
var annotationStorageKey = 'exam-review-annotations-v1:' + location.pathname;

// 抑制 PDF.js 字体加载警告（常见于嵌入字体，不影响显示）
(function() {{
    var origWarn = console.warn;
    console.warn = function(msg) {{
        if (typeof msg === 'string' && msg.indexOf('Failed to load font') >= 0) return;
        origWarn.apply(console, arguments);
    }};
}})();

var canvas = document.getElementById('pdfCanvas');
var ctx = canvas.getContext('2d');

function cloneData(obj) {{
    return JSON.parse(JSON.stringify(obj || {{}}));
}}

function loadAnnotationStorage() {{
    try {{
        var raw = localStorage.getItem(annotationStorageKey);
        if (!raw) return {{}};
        var parsed = JSON.parse(raw);
        return parsed && typeof parsed === 'object' ? parsed : {{}};
    }} catch (e) {{
        console.warn('Failed to read saved annotations:', e);
        return {{}};
    }}
}}

function saveAnnotationStorage() {{
    try {{
        var all = loadAnnotationStorage();
        all[currentFile] = {{
            pageNum: pageNum,
            highlights: cloneData(highlights),
            textNotes: cloneData(textNotes)
        }};
        localStorage.setItem(annotationStorageKey, JSON.stringify(all));
    }} catch (e) {{
        console.warn('Failed to save annotations:', e);
    }}
}}

function loadSavedState(fileKey) {{
    var all = loadAnnotationStorage();
    if (all[fileKey] && typeof all[fileKey] === 'object') {{
        return {{
            pageNum: all[fileKey].pageNum || 1,
            highlights: cloneData(all[fileKey].highlights),
            textNotes: cloneData(all[fileKey].textNotes)
        }};
    }}
    return null;
}}

// ===== PDF 加载 & 切换 =====

function loadPDF(fileKey, pageToRender) {{
    var config = PDF_CONFIG[fileKey];
    if (!config) {{ console.error('Unknown PDF key:', fileKey); return; }}
    var url = encodeURI(config.file);
    var savedState = loadAnnotationStorage()[fileKey] ? loadSavedState(fileKey) : null;
    document.getElementById('pdfLoading').style.display = 'block';
    document.getElementById('pdfError').style.display = 'none';

    if (pdfDocs[fileKey]) {{
        pdfDoc = pdfDocs[fileKey];
        document.getElementById('pdfLoading').style.display = 'none';
        document.getElementById('totalPages').textContent = '/ ' + pdfDoc.numPages + ' 页';
        if (savedState) {{
            highlights = cloneData(savedState.highlights);
            textNotes = cloneData(savedState.textNotes);
        }}
        pageNum = Math.max(1, Math.min(pageToRender || (savedState && savedState.pageNum) || 1, pdfDoc.numPages));
        renderPage(pageNum);
        return;
    }}

    pdfjsLib.getDocument(url).promise.then(function(doc) {{
        pdfDocs[fileKey] = doc;
        pdfDoc = doc;
        document.getElementById('totalPages').textContent = '/ ' + doc.numPages + ' 页';
        document.getElementById('pdfLoading').style.display = 'none';
        if (savedState) {{
            highlights = cloneData(savedState.highlights);
            textNotes = cloneData(savedState.textNotes);
        }}
        pageNum = Math.max(1, Math.min(pageToRender || (savedState && savedState.pageNum) || 1, doc.numPages));
        renderPage(pageNum);
    }}).catch(function(err) {{
        console.error('PDF load error:', err);
        document.getElementById('pdfLoading').style.display = 'none';
        document.getElementById('pdfError').style.display = 'block';
    }});
}}

function switchPDF(fileKey) {{
    if (fileKey === currentFile && pdfDoc) return;
    // 保存当前状态
    if (pdfDoc) {{
        fileStates[currentFile] = {{
            pageNum: pageNum,
            highlights: cloneData(highlights),
            textNotes: cloneData(textNotes)
        }};
        saveAnnotationStorage();
    }}
    currentFile = fileKey;
    document.getElementById('pdfSelector').value = fileKey;
    var state = fileStates[fileKey];
    highlights = state ? cloneData(state.highlights) : {{}};
    textNotes = state ? cloneData(state.textNotes) : {{}};
    loadPDF(fileKey, state ? state.pageNum : 1);
}}

// ===== 渲染（含 HiDPI）=====

function renderPage(num) {{
    if (pageRendering || !pdfDoc) return;
    pageRendering = true;

    var textLayerDiv = document.getElementById('textLayer');
    textLayerDiv.innerHTML = '';

    pdfDoc.getPage(num).then(function(page) {{
        var viewport = page.getViewport({{ scale: scale }});
        currentScale = viewport.scale;
        currentPageWidth = viewport.width;
        currentPageHeight = viewport.height;
        var outputScale = window.devicePixelRatio || 1;
        canvas.width = Math.floor(viewport.width * outputScale);
        canvas.height = Math.floor(viewport.height * outputScale);
        canvas.style.width = viewport.width + 'px';
        canvas.style.height = viewport.height + 'px';

        var renderContext = {{
            canvasContext: ctx,
            viewport: viewport,
            transform: outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null
        }};

        return page.render(renderContext).promise.then(function() {{
            return page.getTextContent().then(function(textContent) {{
                textLayerDiv.style.width = viewport.width + 'px';
                textLayerDiv.style.height = viewport.height + 'px';
                textLayerDiv.style.setProperty('--scale-factor', viewport.scale);
                var task = pdfjsLib.renderTextLayer({{
                    textContentSource: textContent,
                    container: textLayerDiv,
                    viewport: viewport,
                    textDivs: [],
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
        restoreHighlights(num);
        restoreTextNotes(num);
        saveAnnotationStorage();
    }}).catch(function(err) {{
        pageRendering = false;
        console.error('Render error:', err);
    }});
}}

// ===== 高亮标记（Overlay 方案）=====

function rectsOverlap(a, b, sfA, sfB) {{
    sfA = sfA || 1; sfB = sfB || 1;
    for (var i = 0; i < a.length; i++) {{
        var ax = a[i].left * sfA, ay = a[i].top * sfA, aw = a[i].width * sfA, ah = a[i].height * sfA;
        for (var j = 0; j < b.length; j++) {{
            var bx = b[j].left * sfB, by = b[j].top * sfB, bw = b[j].width * sfB, bh = b[j].height * sfB;
            if (ax < bx + bw && ax + aw > bx && ay < by + bh && ay + ah > by) return true;
        }}
    }}
    return false;
}}

function restoreHighlights(num) {{
    var overlay = document.getElementById('highlightLayer');
    overlay.innerHTML = '';
    var recs = highlights[num] || [];
    if (recs.length === 0) return;
    recs.forEach(function(rec) {{
        var sf = currentScale / rec.scale;
        rec.rects.forEach(function(r) {{
            var d = document.createElement('div');
            d.className = 'hl-rect';
            d.style.left = (r.left * sf) + 'px';
            d.style.top = (r.top * sf) + 'px';
            d.style.width = (r.width * sf) + 'px';
            d.style.height = (r.height * sf) + 'px';
            overlay.appendChild(d);
        }});
    }});
}}

function restoreTextNotes(num) {{
    var layer = document.getElementById('annotationLayer');
    layer.innerHTML = '';
    activeNoteId = null;
    var notes = textNotes[num] || [];
    notes.forEach(function(note) {{
        layer.appendChild(buildNoteElement(note));
    }});
}}

function buildNoteElement(note) {{
    var noteEl = document.createElement('div');
    noteEl.className = 'text-note';
    noteEl.dataset.noteId = note.id;
    positionNoteElement(noteEl, note);

    var header = document.createElement('div');
    header.className = 'text-note-header';
    header.innerHTML = '<span>页内笔记</span>';

    var delBtn = document.createElement('button');
    delBtn.className = 'text-note-delete';
    delBtn.type = 'button';
    delBtn.title = '删除文本框';
    delBtn.textContent = '×';
    delBtn.onclick = function(e) {{
        e.stopPropagation();
        deleteTextNote(note.id);
    }};
    header.appendChild(delBtn);

    var body = document.createElement('textarea');
    body.className = 'text-note-body';
    body.placeholder = '输入这一页的补充笔记...';
    body.value = note.text || '';
    body.addEventListener('input', function() {{
        updateTextNote(note.id, {{ text: body.value }});
    }});
    body.addEventListener('focus', function() {{
        setActiveNote(note.id);
    }});

    var resizer = document.createElement('div');
    resizer.className = 'text-note-resizer';

    noteEl.appendChild(header);
    noteEl.appendChild(body);
    noteEl.appendChild(resizer);
    noteEl.addEventListener('mousedown', function() {{
        setActiveNote(note.id);
    }});

    attachNoteDrag(header, noteEl, note.id);
    attachNoteResize(resizer, noteEl, note.id);
    return noteEl;
}}

function positionNoteElement(noteEl, note) {{
    noteEl.style.left = (note.left * currentPageWidth) + 'px';
    noteEl.style.top = (note.top * currentPageHeight) + 'px';
    noteEl.style.width = Math.max(120, note.width * currentPageWidth) + 'px';
    noteEl.style.height = Math.max(72, note.height * currentPageHeight) + 'px';
}}

function getCurrentPageNotes() {{
    if (!textNotes[pageNum]) textNotes[pageNum] = [];
    return textNotes[pageNum];
}}

function getTextNoteById(noteId) {{
    var notes = getCurrentPageNotes();
    for (var i = 0; i < notes.length; i++) {{
        if (notes[i].id === noteId) return notes[i];
    }}
    return null;
}}

function updateTextNote(noteId, patch) {{
    var note = getTextNoteById(noteId);
    if (!note) return;
    Object.assign(note, patch || {{}});
    saveAnnotationStorage();
}}

function setActiveNote(noteId) {{
    activeNoteId = noteId;
    var nodes = document.querySelectorAll('.text-note');
    nodes.forEach(function(node) {{
        node.classList.toggle('selected', node.dataset.noteId === noteId);
    }});
}}

function insertTextNote() {{
    if (!pdfDoc || !currentPageWidth || !currentPageHeight) return;
    var notes = getCurrentPageNotes();
    var note = {{
        id: 'note_' + Date.now() + '_' + notes.length,
        left: Math.min(0.72, 0.08 + (notes.length % 4) * 0.04),
        top: Math.min(0.75, 0.08 + (notes.length % 5) * 0.04),
        width: 0.26,
        height: 0.16,
        text: ''
    }};
    notes.push(note);
    restoreTextNotes(pageNum);
    setActiveNote(note.id);
    saveAnnotationStorage();
    setTimeout(function() {{
        var el = document.querySelector('.text-note[data-note-id="' + note.id + '"] .text-note-body');
        if (el) el.focus();
    }}, 0);
}}

function deleteTextNote(noteId) {{
    var notes = getCurrentPageNotes().filter(function(note) {{
        return note.id !== noteId;
    }});
    if (notes.length > 0) textNotes[pageNum] = notes;
    else delete textNotes[pageNum];
    restoreTextNotes(pageNum);
    saveAnnotationStorage();
}}

function attachNoteDrag(handle, noteEl, noteId) {{
    handle.addEventListener('mousedown', function(e) {{
        if (e.target.closest('.text-note-delete')) return;
        e.preventDefault();
        e.stopPropagation();
        setActiveNote(noteId);

        var note = getTextNoteById(noteId);
        if (!note) return;
        var startX = e.clientX;
        var startY = e.clientY;
        var startLeft = note.left * currentPageWidth;
        var startTop = note.top * currentPageHeight;
        var widthPx = Math.max(120, note.width * currentPageWidth);
        var heightPx = Math.max(72, note.height * currentPageHeight);

        function onMove(ev) {{
            var nextLeft = Math.max(0, Math.min(startLeft + ev.clientX - startX, currentPageWidth - widthPx));
            var nextTop = Math.max(0, Math.min(startTop + ev.clientY - startY, currentPageHeight - heightPx));
            note.left = nextLeft / currentPageWidth;
            note.top = nextTop / currentPageHeight;
            positionNoteElement(noteEl, note);
        }}

        function onUp() {{
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            saveAnnotationStorage();
        }}

        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    }});
}}

function attachNoteResize(resizer, noteEl, noteId) {{
    resizer.addEventListener('mousedown', function(e) {{
        e.preventDefault();
        e.stopPropagation();
        setActiveNote(noteId);

        var note = getTextNoteById(noteId);
        if (!note) return;
        var startX = e.clientX;
        var startY = e.clientY;
        var startWidth = Math.max(120, note.width * currentPageWidth);
        var startHeight = Math.max(72, note.height * currentPageHeight);
        var leftPx = note.left * currentPageWidth;
        var topPx = note.top * currentPageHeight;

        function onMove(ev) {{
            var nextWidth = Math.max(120, Math.min(startWidth + ev.clientX - startX, currentPageWidth - leftPx));
            var nextHeight = Math.max(72, Math.min(startHeight + ev.clientY - startY, currentPageHeight - topPx));
            note.width = nextWidth / currentPageWidth;
            note.height = nextHeight / currentPageHeight;
            positionNoteElement(noteEl, note);
        }}

        function onUp() {{
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            saveAnnotationStorage();
        }}

        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    }});
}}

// 右键菜单：选中文本 → 高亮 / 已高亮则取消
document.addEventListener('contextmenu', function(e) {{
    if (!e.target.closest('#textLayer')) return;
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) return;
    e.preventDefault();

    var range = sel.getRangeAt(0);
    if (!sel.toString()) return;

    var clientRects = range.getClientRects();
    if (!clientRects || clientRects.length === 0) return;

    var pageContainer = e.target.closest('.pdf-page-container');
    if (!pageContainer) return;
    var containerRect = pageContainer.getBoundingClientRect();

    var rects = [];
    for (var i = 0; i < clientRects.length; i++) {{
        var cr = clientRects[i];
        if (cr.width < 1 || cr.height < 1) continue;
        rects.push({{
            left: cr.left - containerRect.left,
            top: cr.top - containerRect.top,
            width: cr.width,
            height: cr.height
        }});
    }}

    if (!highlights[pageNum]) highlights[pageNum] = [];

    // 检查与已有高亮是否重叠 → 重叠则删除（toggle效果）
    var toRemove = [];
    highlights[pageNum].forEach(function(rec) {{
        if (rectsOverlap(rects, rec.rects, 1, currentScale / rec.scale)) {{
            toRemove.push(rec.id);
        }}
    }});

    if (toRemove.length > 0) {{
        highlights[pageNum] = highlights[pageNum].filter(function(rec) {{
            return toRemove.indexOf(rec.id) === -1;
        }});
        if (highlights[pageNum].length === 0) delete highlights[pageNum];
    }} else {{
        highlights[pageNum].push({{
            id: 'hl_' + Date.now() + '_' + highlights[pageNum].length,
            scale: currentScale,
            rects: rects
        }});
    }}

    restoreHighlights(pageNum);
    saveAnnotationStorage();
    sel.removeAllRanges();
}});

// ===== 页面跳转（核心：支持跨文件）=====

function jumpToPage(fileKey, num) {{
    num = parseInt(num);
    if (isNaN(num)) return;

    if (fileKey && fileKey !== currentFile) {{
        if (pdfDoc) {{
            fileStates[currentFile] = {{
                pageNum: pageNum,
                highlights: cloneData(highlights),
                textNotes: cloneData(textNotes)
            }};
            saveAnnotationStorage();
        }}
        currentFile = fileKey;
        document.getElementById('pdfSelector').value = fileKey;
        highlights = {{}};
        textNotes = {{}};
        loadPDF(fileKey, num);
        return;
    }}

    if (!pdfDoc) return;
    num = Math.max(1, Math.min(num, pdfDoc.numPages));
    renderPage(num);
}}

function prevPage() {{ jumpToPage(null, pageNum - 1); }}
function nextPage() {{ jumpToPage(null, pageNum + 1); }}

// ===== 缩放 =====
function zoomIn() {{ scale = Math.min(scale + 0.1, 3.0); updateZoom(); }}
function zoomOut() {{ scale = Math.max(scale - 0.1, 0.4); updateZoom(); }}
function updateZoom() {{
    document.getElementById('zoomLevel').textContent = Math.round(scale * 100) + '%';
    if (pdfDoc) renderPage(pageNum);
}}

// ===== 键盘快捷键 =====
document.addEventListener('keydown', function(e) {{
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'ArrowLeft') {{ e.preventDefault(); prevPage(); }}
    if (e.key === 'ArrowRight') {{ e.preventDefault(); nextPage(); }}
    if (e.key === '+' || e.key === '=') {{ e.preventDefault(); zoomIn(); }}
    if (e.key === '-') {{ e.preventDefault(); zoomOut(); }}
}});

document.getElementById('pdfViewport').addEventListener('wheel', function(e) {{
    if (e.ctrlKey) {{ e.preventDefault(); if (e.deltaY < 0) zoomIn(); else zoomOut(); }}
}}, {{ passive: false }});

// ===== 搜索 =====
function doSearch() {{
    var query = document.getElementById('searchInput').value.trim().toLowerCase();
    var content = document.getElementById('noteContent');
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
        isDragging = true; divider.classList.add('active');
        document.body.style.cursor = 'col-resize'; document.body.style.userSelect = 'none';
    }});
    document.addEventListener('mousemove', function(e) {{
        if (!isDragging) return;
        var rect = container.getBoundingClientRect();
        var offset = e.clientX - rect.left;
        var dw = 6, minL = 200, minR = 300;
        var leftW = Math.max(minL, Math.min(offset, rect.width - minR - dw));
        var rightW = rect.width - leftW - dw;
        if (rightW < minR) {{ rightW = minR; leftW = rect.width - rightW - dw; }}
        pdfPanel.style.width = leftW + 'px'; pdfPanel.style.flex = 'none';
        notePanel.style.width = rightW + 'px'; notePanel.style.flex = 'none';
    }});
    document.addEventListener('mouseup', function() {{
        if (isDragging) {{
            isDragging = false; divider.classList.remove('active');
            document.body.style.cursor = ''; document.body.style.userSelect = '';
        }}
    }});
}})();

// ===== KaTeX =====
try {{ renderMathInElement(document.getElementById('noteContent'), {{
    delimiters: [{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}],
    throwOnError: false
}}); }} catch(e) {{}}

// ===== 启动 =====
loadPDF(DEFAULT_KEY, 1);
</script>

</body>
</html>
"""
    return html

def build_standalone_html(html_body, page_title):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; background: #f5f7fb; color: #333; }}
  .page {{ max-width: 1000px; margin: 0 auto; min-height: 100vh; background: #fff; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }}
  .header {{ position: sticky; top: 0; z-index: 10; background: #2c3e50; color: #fff; padding: 14px 20px; display: flex; justify-content: space-between; align-items: center; gap: 12px; }}
  .header-title {{ font-size: 18px; font-weight: 700; }}
  .header-actions {{ display: flex; gap: 8px; align-items: center; }}
  .header input {{ padding: 6px 10px; border: 1px solid #555; border-radius: 4px; background: #1a1a1a; color: #fff; width: 180px; font-size: 13px; }}
  .header button {{ background: #3498db; color: #fff; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; }}
  .header button:hover {{ background: #2980b9; }}
  .content {{ padding: 24px 28px 48px; font-size: 15px; line-height: 1.8; }}
  .content h1 {{ font-size: 28px; margin: 0 0 14px; color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 8px; }}
  .content h2 {{ font-size: 22px; margin: 28px 0 12px; color: #e74c3c; border-bottom: 1px solid #e74c3c; padding-bottom: 6px; }}
  .content h3 {{ font-size: 18px; margin: 20px 0 10px; color: #2980b9; background: #eaf2f8; padding: 8px 12px; border-radius: 6px; }}
  .content p, .content li {{ margin: 6px 0; }}
  .content ul, .content ol {{ padding-left: 22px; margin: 8px 0; }}
  .content blockquote {{ border-left: 4px solid #2c3e50; margin: 12px 0; padding: 10px 14px; background: #f0f4f8; color: #555; }}
  .content code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 13px; color: #c0392b; font-family: 'Consolas', monospace; }}
  .content pre {{ background: #1f2430; color: #e6edf3; padding: 14px; border-radius: 8px; overflow-x: auto; margin: 10px 0 16px; }}
  .content pre code {{ background: transparent; color: inherit; padding: 0; }}
  .content table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 14px; border: 1px solid #ddd; }}
  .content th, .content td {{ border: 1px solid #ddd; padding: 8px 10px; vertical-align: top; }}
  .content th {{ background: #34495e; color: #fff; white-space: nowrap; }}
  .content tr:nth-child(even) {{ background: #f8f9fa; }}
  .answer-block {{ margin: 10px 0 18px; border: 1px solid #d7e3f1; border-radius: 8px; background: #f8fbff; overflow: hidden; }}
  .answer-block summary {{ list-style: none; cursor: pointer; padding: 10px 14px; font-weight: 600; color: #1f5f99; background: #eef6ff; user-select: none; }}
  .answer-block summary::-webkit-details-marker {{ display: none; }}
  .answer-block summary::before {{ content: '▶ '; }}
  .answer-block[open] summary::before {{ content: '▼ '; }}
  .answer-content {{ padding: 2px 14px 14px; }}
  .answer-content > :first-child {{ margin-top: 8px; }}
  .highlight-match {{ background: #ffff99; padding: 0 2px; }}
  @media (max-width: 700px) {{
    .header {{ flex-direction: column; align-items: stretch; }}
    .header-actions {{ width: 100%; }}
    .header input {{ width: 100%; flex: 1; }}
    .content {{ padding: 18px 16px 36px; }}
  }}
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="header-title">📝 {page_title}</div>
    <div class="header-actions">
      <input type="text" id="searchInput" placeholder="搜索题目/答案..." onkeyup="if(event.key==='Enter')doSearch()">
      <button onclick="doSearch()">搜索</button>
      <button onclick="clearSearch()">清空</button>
    </div>
  </div>
  <div class="content" id="noteContent">
{html_body}
  </div>
</div>
<script>
function isAnswerStart(el) {{
    if (!el) return false;
    var text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
    return text.startsWith('答案：') || text.startsWith('答案要点：') || text.startsWith('参考答案：');
}}

function wrapAnswers() {{
    var content = document.getElementById('noteContent');
    if (!content) return;
    var headings = content.querySelectorAll('h4');
    headings.forEach(function(heading) {{
        var current = heading.nextElementSibling;
        var answerStart = null;
        while (current && current.tagName !== 'H2' && current.tagName !== 'H3' && current.tagName !== 'H4' && current.tagName !== 'HR') {{
            if (isAnswerStart(current)) {{
                answerStart = current;
                break;
            }}
            current = current.nextElementSibling;
        }}
        if (!answerStart) return;
        if (answerStart.previousElementSibling && answerStart.previousElementSibling.classList && answerStart.previousElementSibling.classList.contains('answer-block')) return;

        var details = document.createElement('details');
        details.className = 'answer-block';
        var summary = document.createElement('summary');
        summary.textContent = '点击展开答案';
        var answerContent = document.createElement('div');
        answerContent.className = 'answer-content';
        details.appendChild(summary);
        details.appendChild(answerContent);
        answerStart.parentNode.insertBefore(details, answerStart);

        current = answerStart;
        while (current && current.tagName !== 'H2' && current.tagName !== 'H3' && current.tagName !== 'H4' && current.tagName !== 'HR') {{
            var next = current.nextElementSibling;
            answerContent.appendChild(current);
            current = next;
        }}
    }});
}}

function doSearch() {{
    var query = document.getElementById('searchInput').value.trim().toLowerCase();
    var content = document.getElementById('noteContent');
    content.innerHTML = content.innerHTML.replace(/<span class="highlight-match">(.*?)<\\/span>/g, '$1');
    if (!query) return;
    var walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT, null, false);
    var nodes = [];
    while (walker.nextNode()) {{
        var node = walker.currentNode;
        if (!node.nodeValue.trim()) continue;
        if (node.parentNode && node.parentNode.classList && node.parentNode.classList.contains('highlight-match')) continue;
        if (node.parentNode && ['SCRIPT', 'STYLE'].includes(node.parentNode.tagName)) continue;
        nodes.push(node);
    }}
    nodes.forEach(function(node) {{
        var text = node.nodeValue;
        var lower = text.toLowerCase();
        var idx = lower.indexOf(query);
        if (idx >= 0) {{
            var span = document.createElement('span');
            span.innerHTML = text.slice(0, idx) + '<span class="highlight-match">' + text.slice(idx, idx + query.length) + '</span>' + text.slice(idx + query.length);
            node.parentNode.replaceChild(span, node);
        }}
    }});
}}
function clearSearch() {{
    document.getElementById('searchInput').value = '';
    var c = document.getElementById('noteContent');
    c.innerHTML = c.innerHTML.replace(/<span class="highlight-match">(.*?)<\\/span>/g, '$1');
}}
document.addEventListener('DOMContentLoaded', function() {{
    wrapAnswers();
    if (window.renderMathInElement) {{
        renderMathInElement(document.body, {{
            delimiters: [
                {{left: '$$', right: '$$', display: true}},
                {{left: '$', right: '$', display: false}},
                {{left: '\\(', right: '\\)', display: false}},
                {{left: '\\[', right: '\\]', display: true}}
            ],
            throwOnError: false
        }});
    }}
}});
</script>
</body>
</html>
"""

# ============================================================
# CLI 入口
# ============================================================

def main():
    if "--scan" in sys.argv:
        scanned = auto_scan_pdfs(".")
        if not scanned:
            print("⚠️  未在当前目录找到 PDF 文件。")
            sys.exit(1)
        print_config_template(scanned)
        sys.exit(0)

    input_md = INPUT_MD
    output_html = OUTPUT_HTML
    page_title = PAGE_TITLE
    page_layout = PAGE_LAYOUT

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--scan":
            i += 1
            continue
        if arg == "--input" and i + 1 < len(args):
            input_md = args[i + 1]
            i += 2
            continue
        if arg == "--output" and i + 1 < len(args):
            output_html = args[i + 1]
            i += 2
            continue
        if arg == "--title" and i + 1 < len(args):
            page_title = args[i + 1]
            i += 2
            continue
        if arg == "--layout" and i + 1 < len(args):
            page_layout = args[i + 1]
            i += 2
            continue
        print(f"❌ 不支持的参数: {arg}")
        sys.exit(1)

    if page_layout not in {"split", "standalone"}:
        print(f"❌ 不支持的布局: {page_layout}（可选：split / standalone）")
        sys.exit(1)

    if not os.path.exists(input_md):
        print(f"❌ 未找到笔记文件: {input_md}")
        sys.exit(1)

    with open(input_md, "r", encoding="utf-8") as f:
        md_content = f.read()

    md_content = re.sub(r'!\[.*?\]\(.*?\)', '', md_content)

    html_body = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'codehilite'],
        extension_configs={'codehilite': {'css_class': 'highlight'}}
    )

    html_body = add_page_links(html_body, PDF_FILES, DEFAULT_PDF_KEY)
    if page_layout == "standalone":
        html = build_standalone_html(html_body, page_title)
    else:
        html = build_html(html_body, PDF_FILES, DEFAULT_PDF_KEY, page_title)

    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 已生成: {output_html}")
    print(f"   来源 Markdown: {input_md}")
    print(f"   页面标题: {page_title}")
    print(f"   页面布局: {page_layout}")
    if page_layout == "split":
        print(f"   PDF 配置: {len(PDF_FILES)} 个文件")
        print(f"   默认 PDF: {DEFAULT_PDF_KEY}")
        print()
        print("⚠️  请用 HTTP 服务器打开：")
        print()
        print("   python3 -m http.server 8080")
        print(f"   浏览器访问: http://localhost:8080/{output_html}")
        print()
        print("   功能：← → 翻页  |  Ctrl+滚轮 缩放  |  下拉切换PDF  |  笔记页码跳转")
        print("         右键高亮  |  ＋笔记框页内批注  |  本地自动恢复")
        print("   跨文件跳转：笔记中写「讲义三 p42」即可自动切换PDF+跳转")
    else:
        print()
        print("⚠️  题库页为单栏模式，不显示左侧教材 PDF。")


if __name__ == "__main__":
    main()
