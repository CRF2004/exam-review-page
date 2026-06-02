---
name: exam-review
description: "从教材 PDF 或讲义集合生成考点复习笔记，并输出交互式 HTML 复习页面（支持多 PDF、跨文件页码跳转、PDF页内高亮与文本框笔记）。适用于任意课程的期末复习。Use when user says: 期末复习、考点整理、生成复习页面、复习笔记HTML、exam review page、PDF复习"
argument-hint: [pdf-path-or-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebFetch, WebSearch
---

# Exam Review: PDF / Lecture Notes → Interactive Review Page

从教材PDF生成考点复习笔记和交互式HTML复习页面。支持**多个PDF同时配置**，笔记中可用 `讲义N p42` 格式实现跨文件页码跳转，并支持在左侧 PDF 上进行页内高亮和文本框笔记。
把课程教材、讲义或补充阅读整理成：
- `复习笔记_考点版.md`
- `复习笔记_考点版.html`

其中 HTML 页面默认使用**双栏模式**：左侧 PDF，右侧复习笔记。

## Inputs
- `$ARGUMENTS`：单个 PDF、PDF 目录，或课程材料所在目录
- 可选：用户给出的考试范围、考点提纲、重点章节、题型信息

## Workflow

### Step 1: 扫描材料
如果用户提供目录，先扫描其中 PDF：

```bash
python3 generate_review_page.py --scan
```

目标是确认：
- 有哪些 PDF
- 哪些适合作为主教材 / 讲义 / 参考资料
- 笔记里后续要用哪些文件标识（如 `讲义二 p42`）

### Step 2: 确认复习范围
优先从用户处或材料中确定：
- 考试章节
- 高频题型（选择 / 填空 / 简答 / 计算 / 综合）
- 明确重点与非重点

如果没有现成大纲，就从 PDF 目录、章节标题和老师强调内容中反推考试范围。

### Step 3: 提炼考点笔记
生成 `复习笔记_考点版.md`，推荐内容包括：
- 核心定义
- 关键公式 / 结论
- 典型例子
- 易错点 / 对比点
- 对应教材页码
- 常见考法

页码写法要求：
- 默认 PDF：`p105`
- 跨文件 PDF：`讲义三 p42`
- 范围：`讲义三 p42-p48`

### Step 4: 配置生成器
编辑 `generate_review_page.py` 顶部的 `PDF_FILES`：

```python
PDF_FILES = {
    "default": {"file": "materials/course-material.pdf", "offset": 0, "label": "默认资料"},
    "讲义一": {"file": "materials/lecture1.pdf", "offset": 0, "label": "讲义一：导论"},
    "讲义二": {"file": "materials/lecture2.pdf", "offset": 0, "label": "讲义二：核心方法"},
}
DEFAULT_PDF_KEY = "default"
```

建议优先保持 `offset = 0`，直接把笔记页码写成 PDF 页码。

### Step 5: 生成 HTML

```bash
python3 generate_review_page.py \
  --input 复习笔记_考点版.md \
  --output 复习笔记_考点版.html \
  --title "课程复习笔记" \
  --layout split
```

### Step 6: 启动本地访问

```bash
cd WORK_DIR
python3 generate_review_page.py
```

生成后的 HTML 默认包含以下 PDF 批注能力：
- **右键高亮**：选中文本后右键切换荧光笔高亮
- **文本框笔记**：点击工具栏的 `＋笔记框` 在当前页插入可编辑文本框
- **拖拽与缩放**：文本框可拖动、可调整大小，并随 PDF 缩放/翻页保持相对位置
- **本地持久化**：高亮和文本框会保存在浏览器 `localStorage`，刷新后仍可恢复

注意：
- 这些批注**不会写入原始 PDF 文件**
- 它们属于网页层叠加笔记；换浏览器、清缓存、换设备后可能丢失

### Step 8: 启动 HTTP 服务器并提示用户

```bash
cd WORK_DIR
python3 -m http.server 8080
```

然后访问：

```text
http://localhost:8080/复习笔记_考点版.html
```

## Output standard

最终的 `复习笔记_考点版.md` 应该适合考试复习，而不只是材料摘抄。标准是：
- 能快速浏览
- 能直接背诵
- 能按页码回到原 PDF
- 能衔接题库生成

用户打开页面后可：
1. **左侧 PDF 面板**：工具栏下拉框可切换不同PDF，← → 翻页，Ctrl+滚轮缩放
2. **跨文件跳转**：点击笔记中的 `讲义三 p42` 链接，自动切换到对应PDF并跳转至指定页
3. **笔记搜索**：右上角搜索框实时高亮笔记内容
4. **面板拖拽**：中间分隔条可拖拽调整左右面板宽度
5. **右键高亮**：在PDF文字上选中文本后右键，可添加荧光笔高亮
6. **页内文本框笔记**：点击 `＋笔记框` 可在当前 PDF 页上添加、编辑、拖拽、缩放文本框
7. **本地恢复**：刷新页面后，当前浏览器中的高亮和文本框笔记会自动恢复

## Integration with other skills

- 如果输入是课堂转写，建议先用 `lecture-transcript-review`
- 如果已经有考点笔记并想继续出题，接着用 `exam-question-bank`

## Notes

- 这是一个通用 skill，不应把仓库默认配置写死成某一门课。
- 课程私有内容更适合放在使用示例或用户自己的工作目录里。
- 如需题库页，应使用 `--layout standalone`，但那属于 `exam-question-bank` 的工作流。

用户反馈问题后可能需要的修复：
- **公式渲染问题**：md转html时 `|` 在LaTeX中破坏表格 → 替换为 `\lVert`/`\lvert`
- **公式渲染问题**：`<` 被解析为HTML标签 → 替换为 `\lt`
- **缩放敏感度**：调整 `zoomIn/Out` 步长（目前±0.1）
- **页码映射不准确**：重新验证 offset 值
- **PDF载入问题**：确认是否使用了 http://localhost:8080 而非 file:// 协议
- **批注丢失**：确认未清除浏览器本地存储；如需跨设备，后续可加导出/导入批注
