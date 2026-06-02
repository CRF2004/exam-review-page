---
name: lecture-transcript-review
description: "将课堂录音转写/ASR 文本整理为可复习的课程摘要、完整知识点和结构化中间产物；适用于期末复习、课堂录音整理、讲义转写提炼，并可衔接 exam-review 页面生成。Use when user says: 课堂录音转文字、课程摘要、知识点提取、期末复习整理、lecture transcript review、ASR notes extraction"
argument-hint: [transcript-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Agent, WebFetch, WebSearch
---

# Lecture Transcript Review

把课堂录音转写文本整理成**可直接复习**的笔记，而不是只保留原始 ASR 文本。

**Inputs**
- `$ARGUMENTS`：转写目录路径，通常包含多个 `.txt` 文件
- 可选：课程名称、考试范围、老师给出的重点章节

**Recommended outputs**
- `课程摘要与知识点.md`：给学生直接复习的主文档
- `extraction_pipeline.md`：抽取流程说明
- `extracted/structured_lessons.json`：结构化中间结果
- `extracted/structured_lessons.md`：结构化概览

## Goal

把口语化、重复、噪声较多的课堂转写，提炼为两层内容：
1. **课程摘要**：每节课讲了什么、主线是什么、和前后课程如何衔接
2. **完整知识点**：定义、结论、例子、模型、易错点、潜在考点

## Workflow

### Step 1: Inspect files and detect anomalies

先扫描目录，确认：
- 有哪些 `.txt` 转写文件
- 文件是否为空
- 是否存在明显误放的异源文件
- 是否已有脚本或中间产物可复用

建议检查：
- 文件名列表
- 文件大小/字数
- 前 50~100 行样例
- 是否包含统一结构（时间、关键词、正文、说话人标签）

如果发现某个文件主题明显偏离课程主线，应标记为**疑似误放文件**，不要直接混入复习主干。

### Step 2: Normalize transcripts

对每份转写做轻量清洗：
- 删除 `说话人 1 00:00` 这类噪声标签
- 合并多余空白
- 保留原始段落顺序
- 如果文件包含 `日期 | 时长 / 关键词 / 文字记录` 结构，按段切开

不要过度“润色”原文；目标是保留课程信息，不是改写成散文。

### Step 3: Build structured lesson records

对每个文件提取：
- 文件名
- 课程标题（可由文件名推断）
- 分段标题/时间戳
- 原始关键词
- 清洗后的正文
- 字数
- 高频课程术语

如果仓库里没有现成脚本，可生成一个轻量脚本，把结果输出成 JSON + Markdown，便于后续人工核查。

## Suggested script behavior

脚本建议支持：
```bash
python3 scripts/extract_lessons.py --input . --output extracted
```

建议输出：
- `extracted/structured_lessons.json`
- `extracted/structured_lessons.md`

JSON 适合后续二次处理；Markdown 适合快速人工检查。

### Step 4: Extract per-lesson meaning

对每节课生成固定模板：
- 本节主题
- 核心概念
- 关键结论
- 课堂案例
- 可能考点
- 与上一讲/下一讲的连接

优先提炼**老师反复强调**的内容：
- 定义
- 条件
- 分类
- 结论
- 比较关系
- 典型例子

### Step 5: Merge across lessons

把所有单节结果融合成总复习框架，通常按以下层次组织：
- 基础概念层
- 方法/模型层
- 经典例子层
- 高频考点层
- 期末作答建议层

目标不是“按时间顺序堆材料”，而是“按复习逻辑重组材料”。

### Step 6: Produce the study-facing document

主文档 `课程摘要与知识点.md` 建议包含：
- 数据清洗说明
- 逐讲课程摘要
- 整门课知识框架
- 高频关系/对比
- 课堂案例对应知识点
- 期末复习建议
- 数据缺口说明

文档风格要求：
- 语言简洁，适合背诵和翻看
- 从“原始课堂话语”转换成“考试可用表达”
- 明确区分：定义、结论、例子、应用、易错点

### Step 7: Quality checks

交付前至少核查：
- 空文件是否已剔除
- 异源文件是否已标记
- 每节课是否都有摘要
- 总知识框架是否覆盖主要章节
- 主文档是否真的适合复习，而不是只是“转写摘要”

## Extraction heuristics

### What to keep
- 老师定义概念时的稳定表达
- 对模型之间的比较
- 课堂中重复出现的术语
- 典型案例及其对应理论
- 老师直接提示“要注意”“可能会考”“必须掌握”的内容

### What to compress
- 口头停顿词
- 大量重复的口语引导语
- 与主线无关的闲聊
- 纯组织性课堂事务（除非影响考试）

### What to flag
- 文件为空
- 文件损坏
- 主题不属于当前课程
- 专有名词疑似 ASR 识别错误

## Output format example

### 逐讲摘要模板

```markdown
### `3_16.txt`：协调博弈、零和博弈、最大最小、斗鸡博弈

**本节主线**
- ...

**本节关键词**
- ...

**本节结论**
- ...
```

### 总知识框架模板

```markdown
## 二、整门课知识框架

### 1. 基本概念
- ...

### 2. 关键均衡概念
- ...

### 3. 重要博弈类型
- ...
```

## Integration with this repository

如果用户后续还想生成交互式复习页：
1. 先用本 skill 从转写生成 `课程摘要与知识点.md`
2. 再把其中适合展示的内容重写为 `复习笔记_考点版.md`
3. 最后交给仓库现有的 `exam-review` 工作流和 `generate_review_page.py`

也就是说，这个 skill 更适合处理：
- **输入侧**：课堂转写、录音 ASR、讲课文本

而现有 `exam-review` skill 更适合处理：
- **展示侧**：PDF + 考点笔记 → HTML 交互复习页

## Minimal command checklist

```bash
# 1) 浏览转写目录
rg --files .

# 2) 运行结构化抽取脚本
python3 scripts/extract_lessons.py --input . --output extracted

# 3) 生成/更新复习主文档
# 输出为 课程摘要与知识点.md
```

## Notes

- 优先做**结构化抽取 + 复习导向整理**，不要一开始就做页面。
- 如果课程文件中混入其他学科内容，必须显式说明排除依据。
- 如果用户的目标是期末复习，最终交付应以“能背、能查、能答题”为标准。