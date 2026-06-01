# Interactive Exam Review Page Generator

根据教材 PDF 自动生成交互式复习页面：**左栏 PDF 教材 + 右栏考点笔记**，支持**多 PDF 切换**、**跨文件页码跳转**、**荧光笔高亮**和**全文搜索**。

适用于任何学科的期末复习——只需提供 PDF 教材和考点笔记，即可生成一份可交互的 HTML 复习页面。

## 效果预览

![复习页面截图](image.png)

*左栏：PDF 教材（下拉切换多文件、缩放、翻页）；右栏：考点笔记（搜索、公式渲染、页码跳转）*

## 功能特性

### 核心功能
- **左右分栏**：左侧 PDF 教材，右侧考点笔记，中间分隔条可拖拽调整宽度
- **多 PDF 支持**：工具栏下拉框切换不同教材，各自独立记忆页码位置和高亮记录
- **跨文件页码跳转**：笔记中写 `讲义三 p42` 即可点击后自动切换到对应 PDF 并跳转指定页
- **页码跳转**：点击笔记中的页码链接（如 `p105`），PDF 自动跳转到对应页

### 阅读辅助
- **缩放控制**：工具栏 +/- 按钮，或 Ctrl+滚轮缩放（步长 0.1）
- **键盘快捷键**：← → 翻页，+/- 缩放
- **笔记搜索**：实时搜索高亮笔记内容，支持 Enter 触发和清除
- **公式渲染**：KaTeX 渲染 LaTeX 行内公式 `$...$` 和块级公式 `$$...$$`

### 高亮标记
- **右键荧光笔高亮**：在 PDF 文字上选中文本后右键，自动添加半透明黄色荧光笔高亮（Overlay 方案，不破坏 PDF 渲染）
- **切换取消**：选中已高亮区域再次右键可取消高亮
- **缩放适配**：高亮位置在不同缩放级别下自动适配

### 自适应
- **HiDPI/Retina 支持**：自动适配高分屏，文字清晰
- **响应式布局**：移动端自动切换为上下排列

## 使用方法

### 1. 准备目录

```
your-project/
├── 教材1.pdf                # PDF 教材文件（可多个）
├── 教材2.pdf
├── 复习笔记_考点版.md        # 考点笔记（格式见下方说明）
└── generate_review_page.py  # 本仓库的生成脚本
```

### 2. 配置脚本

编辑 `generate_review_page.py` 顶部的 `PDF_FILES` 配置：

```python
PDF_FILES = {
    "讲义一":  {"file": "博弈论补充讲义（一）.pdf", "offset": 0, "label": "讲义一：基础理论"},
    "讲义二":  {"file": "博弈论补充讲义（二）.pdf", "offset": 0, "label": "讲义二：理性假设"},
    "讲义三":  {"file": "博弈论补充讲义（三）.pdf", "offset": 0, "label": "讲义三：静态博弈"},
    # ... 按需增减
}
DEFAULT_PDF_KEY = "讲义一"
```

每个配置项含义：

| 字段 | 说明 |
|------|------|
| **key**（字典键名） | 笔记中跨文件引用的标识，如 `讲义三 p42` 中的"讲义三"，必须是中文字符 |
| **file** | PDF 文件名（相对于脚本的路径，可在子目录如 `materials/xxx.pdf`） |
| **offset** | 页码偏移量。**建议统一设为 0**，即笔记中的 `p10` 直接对应 PDF 第 10 页 |
| **label** | 左侧工具栏下拉框中显示的名称 |

### 3. 生成 HTML

```bash
pip install markdown
python3 generate_review_page.py
```

### 4. 启动 HTTP 服务器

```bash
python3 -m http.server 8080
```

浏览器打开 `http://localhost:8080/复习笔记_考点版.html`

> ⚠️ 浏览器安全策略限制 `file://` 协议加载 PDF。请使用 HTTP 服务器（如上述命令）或用 Firefox 打开。

### 5. 使用方式

- **切换 PDF**：左上角下拉框选择不同教材
- **翻页**：◀ ▶ 按钮 或 ← → 方向键
- **缩放**：+/- 按钮 或 Ctrl+滚轮
- **搜索笔记**：右上角搜索框输入关键词，Enter 触发
- **跳转页码**：点击笔记中的 `p105` 或 `讲义三 p42` 链接
- **荧光笔高亮**：在左侧 PDF 上选中文字 → 右键 → 自动高亮；再次右键同一位置取消

## 考点笔记格式

`复习笔记_考点版.md` 使用 markdown 表格组织，每条考点包含：

| 项目 | 内容 |
|------|------|
| **核心内容** | 公式、定义、概念（LaTeX 用 `$...$` / `$$...$$` 包围） |
| **对应教材** | 文件标识 + PDF页码，如 `讲义三 p10-p12` |
| **常见考法** | 题型标注：🅰选择/🅱简答/🅲计算 |
| **💡 记忆点** | 口诀、对比、类比帮助记忆 |

### 页码标注规范

- **页码使用 PDF 文件页码**（第 1 页即 PDF 第 1 页），与教材印刷页码无关
- **确保 offset=0**，笔记中的 `p10` 对应 PDF 第 10 页
- 确定页码的推荐方法见下方的【精确标定页码】章节

### 跨文件引用

笔记中支持两种页码引用格式：

| 格式 | 示例 | 行为 |
|------|------|------|
| `p105` | 当前教材第105页 | 跳转当前 PDF 到 105 页 |
| `讲义三 p42` | 讲义三第42页 | **自动切换**到"讲义三"PDF 并跳转 42 页 |

> 文件标识（如"讲义三"）必须与 `PDF_FILES` 配置中的键名完全一致。

### 范围写法

支持页码范围语法 `pN-pM`，同一个范围内的两个页码都指向同一份 PDF：

```
讲义三 p6-p10   →  p6 和 p10 都跳转讲义三
讲义四 p3-p5    →  p3 和 p5 都跳转讲义四
```

### 表格注意事项

- 不要在 LaTeX 公式中使用 `|` 管道符（会破坏 markdown 表格），改用 `\lVert` `\rVert` `\lvert` `\rvert`
- 不要在 LaTeX 公式中使用 `<` 号（可能导致 HTML 标签解析错误），改用 `\lt`
- 所有 LaTeX 公式用 `$` 或 `$$` 包围

## 精确标定页码（关键词搜索法）

编写考点笔记时，使用关键词搜索精确确定每个考点对应的页码：

```python
import pdfplumber

# 对每个考点，提取 2~5 个核心关键词，逐页搜索
exam_keywords = {
    "纳什均衡": ["纳什均衡", "Nash equilibrium", "划线法"],
    "占优战略": ["占优战略", "劣战略", "dominant"],
    # ...
}

with pdfplumber.open("教材.pdf") as pdf:
    for i in range(len(pdf.pages)):
        text = pdf.pages[i].extract_text() or ""
        for topic, keywords in exam_keywords.items():
            hits = [kw for kw in keywords if kw in text]
            if hits:
                print(f"p{i+1}: [{topic}] 命中 {hits}")
```

判定原则：
- **核心页**：关键词密集出现的页面
- **范围截止**：连续多页无命中时截断
- **避免"路过"页**：仅在其他话题中被顺带提及的不算

## 命令行工具

```bash
python3 generate_review_page.py                # 使用预设配置生成 HTML
python3 generate_review_page.py --scan          # 扫描当前目录 PDF 并输出配置模板
python3 generate_review_page.py --scan --apply  # 扫描并直接用结果生成
```

## 页面交互说明

### 打开页面后

1. **工具栏**（左栏顶部）：
   - 下拉框选择 PDF 文件（各自独立记忆页码）
   - ◀ ▶ 翻页，中间输入框直接输页码
   - +/- 缩放，显示当前缩放比例

2. **分隔条**：拖拽调整左右面板宽度

3. **笔记面板**（右栏）：
   - 顶部显示"考点笔记"，右侧有搜索框
   - 点击 `p105` 链接 → PDF 跳转 105 页
   - 点击 `讲义三 p42` 链接 → 自动切换 PDF 并跳转 42 页

4. **荧光笔高亮**：在左侧 PDF 文字上选中文本 → 右键 → 自动添加/取消高亮

### 浏览器兼容性

- **Chrome/Edge**：需通过 HTTP 服务器打开（`python3 -m http.server 8080`）
- **Firefox**：可直接 `file://` 打开（但跨文件跳转仍建议使用 HTTP 服务器）
- **移动端**：自动变为上下布局（PDF 在上，笔记在下）

## 技术架构

- **PDF 渲染**：PDF.js（Canvas + Text Layer 叠加）
- **荧光笔高亮**：Overlay 方案（`highlightLayer` div + 绝对定位 `<div class="hl-rect">`，z-index 高于 textLayer）
- **HiDPI**：`window.devicePixelRatio` 缩放 + Canvas transform
- **公式渲染**：KaTeX（自动渲染，`renderMathInElement`）
- **多 PDF 缓存**：`pdfDocs` 对象缓存已加载文档，切换无需重请求
- **页码跳转**：Python 端正则预处理（两轮：先跨文件 `讲义N p\d+`，后单文件 `p\d+`，范围 `pN-pM` 一次性匹配）

## Claude Code Skill 自动生成

本工具的工作流已封装为 Claude Code 的 `exam-review` skill：

```bash
# 在项目目录中运行 Claude Code
/exam-review ./教材目录/
```

skill 会自动完成：
1. 扫描目录下所有 PDF，识别"讲义N"命名模式
2. 分析各 PDF 结构（页数、章节标题）
3. 与你确认考点范围（考试题型、章节、重点）
4. 使用关键词搜索精确定位页码
5. 生成考点笔记 `复习笔记_考点版.md`（含跨文件引用）
6. 配置并运行 `generate_review_page.py`
7. 启动 HTTP 服务器

## 示例

本仓库包含示例文件：
- `generate_review_page.py` — 生成脚本（可配置多 PDF）
- `exam-review.md` — Claude Code skill 定义文件
- 使用该工具生成的完整 HTML 复习页面

## 常见问题

**Q: PDF 加载失败？**
A: 务必使用 HTTP 服务器（`python3 -m http.server 8080`），不要直接双击 HTML 文件打开。Chrome 禁止 `file://` 协议加载 PDF。

**Q: 控制台有字体警告？**
A: PDF.js 的 `"Failed to load font"` 警告是常见的无害警告，不影响显示。脚本已自动抑制此类消息。

**Q: 切换 PDF 很慢？**
A: 脚本内置了 `pdfDocs` 缓存机制。首次加载后，同一切换不会重复请求网络。

**Q: 页码跳转不准确？**
A: 确认笔记中标注的页码是 PDF 文件页码（第 1 页即 PDF 第 1 页），且 offset 设为 0。使用"关键词搜索法"（见上方说明）精确定位。

**Q: 端口 8080 被占用？**
A: 运行 `fuser -k 8080/tcp` 结束占用进程，或换用其他端口（如 `python3 -m http.server 8081`）。
