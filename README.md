# Exam Review Toolkit

一个面向**任意课程**的通用仓库，用来把课程材料整理成适合期末复习的产物。当前仓库主要覆盖三类工作：

1. **教材 / 讲义 PDF → 交互式复习笔记 HTML**
2. **考点笔记 → 结构化题库 + 刷题 HTML**
3. **课堂录音转写 / ASR 文本 → 课程摘要 + 完整知识点**

## 三个 Skill

### 1. `exam-review`
把教材 PDF 和考点笔记组织成**交互式复习页**：左侧 PDF，右侧笔记。

适合：
- 已经有教材 / 讲义 PDF
- 已经有或准备整理 `复习笔记_考点版.md`
- 希望边看 PDF 边看考点

对应文件：
- `exam-review.md`
- `generate_review_page.py`

### 2. `exam-question-bank`
把考点笔记扩展成**结构化题库**，并生成**答案可折叠**的刷题 HTML 页面。

适合：
- 已经有 `复习笔记_考点版.md`
- 想补一套按考点组织的选择 / 填空 / 简答 / 综合题
- 想得到独立的 `期末题库.html`

对应文件：
- `exam-question-bank.md`
- `generate_review_page.py`

### 3. `lecture-transcript-review`
把课堂录音转写、ASR 文本、课堂记录整理成：
- 课程摘要
- 完整知识点
- 结构化中间产物

适合：
- 只有课堂转写，没有正式整理笔记
- 想从原始上课文本提炼出复习材料
- 想先做信息抽取，再进入 HTML 展示或题库生成

对应文件：
- `lecture-transcript-review.md`
- `scripts/extract_lessons.py`（由实际课程目录按需生成）

## 推荐工作流

### 路线 A：你有教材 PDF
1. 用 `exam-review` 生成 `复习笔记_考点版.md`
2. 用 `generate_review_page.py` 生成 `复习笔记_考点版.html`
3. 如需刷题，再用 `exam-question-bank` 生成 `期末题库.md` 和 `期末题库.html`

### 路线 B：你只有课堂转写
1. 先用 `lecture-transcript-review` 抽取 `课程摘要与知识点.md`
2. 把其中适合考试展示的内容整理成 `复习笔记_考点版.md`
3. 再用 `exam-review` 生成交互式复习页
4. 如需刷题，再接 `exam-question-bank`

## 仓库核心文件

- `generate_review_page.py`：通用 HTML 生成器
- `exam-review.md`：复习笔记页面 skill
- `exam-question-bank.md`：题库页面 skill
- `lecture-transcript-review.md`：课堂转写抽取 skill

## `generate_review_page.py` 支持的两种页面

### `split`
双栏模式：左侧 PDF，右侧笔记。

适合：
- `复习笔记_考点版.md`
- 教材联动复习

### `standalone`
单栏模式：不显示 PDF，只显示内容区。

适合：
- `期末题库.md`
- 课程摘要
- 独立整理页

## 快速开始

### 1. 安装依赖

```bash
pip install markdown
```

### 2. 准备文件

```text
your-course/
├── materials/
│   ├── 讲义一.pdf
│   ├── 讲义二.pdf
│   └── 教材.pdf
├── 复习笔记_考点版.md
├── 期末题库.md
└── generate_review_page.py
```

### 3. 先扫描 PDF（可选但推荐）

```bash
python3 generate_review_page.py --scan
```

### 4. 生成复习笔记 HTML

```bash
python3 generate_review_page.py \
  --input 复习笔记_考点版.md \
  --output 复习笔记_考点版.html \
  --title "课程复习笔记" \
  --layout split
```

### 5. 生成题库 HTML

```bash
python3 generate_review_page.py \
  --input 期末题库.md \
  --output 期末题库.html \
  --title "课程期末题库" \
  --layout standalone
```

### 6. 启动本地服务

```bash
python3 -m http.server 8080
```

访问：
- `http://localhost:8080/复习笔记_考点版.html`
- `http://localhost:8080/期末题库.html`

## PDF 配置说明

编辑 `generate_review_page.py` 顶部的 `PDF_FILES`：

```python
PDF_FILES = {
    "default": {"file": "materials/course-material.pdf", "offset": 0, "label": "默认资料"},
    "讲义一": {"file": "materials/讲义一.pdf", "offset": 0, "label": "讲义一：导论"},
    "讲义二": {"file": "materials/讲义二.pdf", "offset": 0, "label": "讲义二：核心方法"},
}
DEFAULT_PDF_KEY = "default"
```

字段含义：
- `key`：笔记中的引用标识，例如 `讲义二 p42`
- `file`：PDF 相对路径
- `offset`：页码偏移量，建议优先保持 `0`
- `label`：页面下拉框显示名称

## 笔记中的页码写法

支持两种格式：

- `p105`：跳转默认 PDF 第 105 页
- `讲义二 p42`：切换到 `讲义二` 后跳到第 42 页

也支持范围写法：
- `讲义二 p42-p48`

## 适合放入仓库的内容

- 任意课程教材 PDF
- 讲义、补充阅读、参考资料
- 课堂转写文本
- 考点整理笔记
- 题库 Markdown

## 典型产物

- `复习笔记_考点版.md`
- `复习笔记_考点版.html`
- `期末题库.md`
- `期末题库.html`
- `课程摘要与知识点.md`
- `extraction_pipeline.md`
- `extracted/structured_lessons.json`
- `extracted/structured_lessons.md`

## 常见问题

**Q: 为什么 PDF 打不开？**  
A: 请用 `python3 -m http.server 8080` 启动本地服务，不要直接双击 HTML 用 `file://` 打开。

**Q: 题库答案为什么没有折叠？**  
A: 请确认题目是 `#### 题N【题型】`，答案块以 `- **答案：**`、`- **答案要点：**` 或 `- **参考答案：**` 开头。

**Q: 课堂转写能直接生成 HTML 吗？**  
A: 建议先用 `lecture-transcript-review` 提炼成适合复习的 Markdown，再交给 `exam-review` 或 `exam-question-bank`。
