---
name: exam-review
description: "从教材PDF生成考点复习笔记 + 交互式HTML复习页面（支持多PDF、跨文件页码跳转）。用户提供PDF教材（单个或多个）和可选考点大纲，自动完成笔记整理、HTML生成、启动本地服务器。Use when user says: 期末复习、考点整理、生成复习页面、复习笔记HTML、exam review page、PDF复习"
argument-hint: [pdf-path]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebFetch, WebSearch
---

# Exam Review: PDF Textbook → Interactive Review Page

从教材PDF生成考点复习笔记和交互式HTML复习页面。支持**多个PDF同时配置**，笔记中可用 `讲义N p42` 格式实现跨文件页码跳转。

**Inputs:**
- `$ARGUMENTS` — PDF教材路径（可选，若提供则自动扫描目录下的PDF）
- 用户提供的考点大纲（可选），可以是文本描述或 markdown 文件

**如果未提供PDF路径**：工具会自动扫描工作目录下所有PDF文件并识别"讲义N"命名模式。

## Workflow

### Step 0: 扫描 PDF 文件

如果用户提供了目录或未指定路径，先用 `--scan` 模式扫描：

```bash
cd WORK_DIR
python3 generate_review_page.py --scan
```

这会输出当前目录下所有 PDF 的配置模板。如果文件和"讲义"命名模式匹配，会自动提取为 `讲义一`、`讲义二` 等键名。

手动确认文件名和键名的映射关系，每个PDF需分配一个**唯一的中文标识**（如"讲义一"、"参考资料"），用于笔记中的跨文件引用。

### Step 1~2: 分析每个 PDF 的结构与内容目录

对每个 PDF 独立分析。使用 pdfplumber（已安装）：

```bash
python3 -c "
import pdfplumber
path = '讲义一.pdf'
with pdfplumber.open(path) as pdf:
    print(f'{path}: {len(pdf.pages)} pages')
    for i in range(min(len(pdf.pages), 20)):
        text = pdf.pages[i].extract_text()[:200] if pdf.pages[i].extract_text() else '(empty)'
        first_line = text.strip().split(chr(10))[0] if text.strip() else '(empty)'
        print(f'PDF page {i+1}: {repr(first_line[:90])}')
"
```

关键信息要提取：
- **总页数**
- **各页主题**：记录每页的章节标题或首行内容，建立内容→页码的概览

> **页码策略**：直接使用 PDF 页码（第1页即PDF文件第1页），offset 统一设为 0。笔记中的 `p42` 即 PDF 第 42 页，与印刷页码无关。

### Step 3: 收集考点信息

向用户确认考点范围，两种方式：

**方式A：用户提供了考点大纲文件**
- 读取并解析大纲，确认涵盖的章节和知识点

**方式B：用户只给了PDF，没有大纲**
- 从各PDF提取章节信息
- 向用户列出可用内容，询问考试范围
- 根据用户反馈确定考点

无论哪种方式，最终需要确认：
- 考试题型（选择/填空/简答/综合/代码）
- 需要覆盖的章节范围
- 重点/必考章节

### Step 4: 精确标定页码（关键词搜索法）

生成考点笔记前，必须用关键词搜索精确定位每个考点的页码。方法：

对每个考点，提取 2~5 个核心关键词，在所有 PDF 中逐页搜索，找出每个词实际出现的页面。

```bash
python3 -c "
import pdfplumber, os
from collections import defaultdict

# 定义考点→关键词映射（根据实际考点修改）
exam_points = {
    '纳什均衡': ['纳什均衡', 'Nash', '划线法', '相互最优'],
    '占优战略': ['占优', '劣战略', 'Dominant'],
    # ... 按实际考点补充
}

base = '.'  # PDF 所在目录
for fname in sorted(os.listdir(base)):
    if not fname.endswith('.pdf'): continue
    path = os.path.join(base, fname)
    with pdfplumber.open(path) as pdf:
        print(f'\\n=== {fname} ===')
        for i in range(len(pdf.pages)):
            text = pdf.pages[i].extract_text() or ''
            for topic, keywords in exam_points.items():
                hits = [kw for kw in keywords if kw in text]
                if hits:
                    first_line = text.strip().split(chr(10))[0][:60]
                    print(f'  p{i+1}: {first_line}')
                    print(f'    → [{topic}] 命中: {\", \".join(hits)}')
"
```

依据搜索结果确定页码范围：
- **核心页**：关键词密集出现的页
- **范围截止**：当连续多页无命中时截断
- **避免"路过"页**：仅在其他话题中被顺带提及的页面不算

### Step 6: 生成考点笔记 (Markdown)

生成 `复习笔记_考点版.md`，格式如下：

```markdown
# 博弈论期末复习笔记（考点版）

> 教材：博弈论补充讲义
> 题型：选择/填空/简答/计算
>
> ⚠️ 页码为 PDF 文件页码（第1页即PDF第1页），与印刷页码无关。

## 一、基础理论

### 考点1：理性人假设

| 项目 | 内容 |
|------|------|
| **核心内容** | ① 完备性：任意两个结果可比较；② 传递性：$A \succ B \land B \succ C \Rightarrow A \succ C$ |
| **对应教材** | 讲义一 p1-p15 |
| **常见考法** | 🅱 简答：理性人假设的内涵 |
| **💡 记忆点** | 完备性=没有"无法比较"，传递性=没有"循环偏好" |
```

**跨文件页码引用**：当笔记引用不同PDF时，在页码前加**文件标识**：

| 格式 | 含义 | 行为 |
|------|------|------|
| `p105` | 当前PDF第105页 | 跳转当前PDF到105页 |
| `讲义三 p42` | 讲义三第42页 | 自动切换到讲义三PDF并跳转42页 |

文件标识必须是 **中文字符**（如 `讲义一`、`参考资料`），并且必须与脚本 `PDF_FILES` 配置中的键名完全一致。

> 页码使用 PDF 文件页码（第1页=PDF第1页），所有 PDF 的 offset 均设为 0。

在末尾附加按题型分类的速查表：
- **选择题/填空题**：考点→核心要点
- **简答题**：考点→关键话术
- **计算题**：考点→关键公式

### 考点笔记编写原则

1. **核心内容**：公式用 LaTeX `$...$` / `$$...$$` 包围
2. **对应教材**：务必标注文件标识和印刷页码，格式 `讲义N pXX-pXX`
3. **常见考法**：用 🅰选择/🅱简答/🅲计算 标注
4. **💡 记忆点**：用对比、口诀、类比帮助记忆
5. **表格注意事项**：
   - 不要在 LaTeX 公式中使用 `|` 管道符（会破坏 markdown 表格），改用 `\lVert` `\rVert` `\lvert` `\rvert`
   - 不要在 LaTeX 公式中使用 `<` 可能导致 HTML 标签解析，改用 `\lt`
   - 所有 LaTeX 公式用 `$` 或 `$$` 包围

### Step 6: 配置 `generate_review_page.py`

从本仓库拷贝 `generate_review_page.py` 到工作目录，编辑顶部的 `PDF_FILES` 配置：

```python
PDF_FILES = {
    "default": {"file": "参考资料.pdf", "offset": 0, "label": "综合参考资料"},
    "讲义一":  {"file": "博弈论补充讲义（一）.pdf", "offset": 0, "label": "讲义一：基础理论"},
    "讲义二":  {"file": "博弈论补充讲义（二）.pdf", "offset": 0, "label": "讲义二：理性假设"},
    # ... 按需增减
}
DEFAULT_PDF_KEY = "default"    # 默认打开的PDF
```

每个配置项含义：
| 字段 | 说明 |
|------|------|
| **key**（字典键名） | 笔记中跨文件引用的标识，如 `讲义三 p42` 中的"讲义三" |
| **file** | PDF 文件名（与脚本同目录） |
| **offset** | PDF页码偏移量（统一设为 0，直接使用PDF页码） |
| **label** | 左侧工具栏下拉框中显示的名称 |

也可以自动扫描：
```bash
python3 generate_review_page.py --scan     # 查看扫描结果
python3 generate_review_page.py --scan --apply  # 直接应用
```

### Step 7: 运行脚本

```bash
cd WORK_DIR
python3 generate_review_page.py
```

### Step 8: 启动 HTTP 服务器并提示用户

```bash
cd WORK_DIR
python3 -m http.server 8080
```

然后在后台运行服务器，并告诉用户访问：
```
http://localhost:8080/复习笔记_考点版.html
```

### 功能速览

用户打开页面后可：
1. **左侧 PDF 面板**：工具栏下拉框可切换不同PDF，← → 翻页，Ctrl+滚轮缩放
2. **跨文件跳转**：点击笔记中的 `讲义三 p42` 链接，自动切换到对应PDF并跳转至指定页
3. **笔记搜索**：右上角搜索框实时高亮笔记内容
4. **面板拖拽**：中间分隔条可拖拽调整左右面板宽度
5. **右键高亮**：在PDF文字上选中文本后右键，可添加荧光笔高亮

### Step 9: 后续优化（按需）

用户反馈问题后可能需要的修复：
- **公式渲染问题**：md转html时 `|` 在LaTeX中破坏表格 → 替换为 `\lVert`/`\lvert`
- **公式渲染问题**：`<` 被解析为HTML标签 → 替换为 `\lt`
- **缩放敏感度**：调整 `zoomIn/Out` 步长（目前±0.1）
- **页码映射不准确**：重新验证 offset 值
- **PDF载入问题**：确认是否使用了 http://localhost:8080 而非 file:// 协议
