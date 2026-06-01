# Interactive Exam Review Page Generator

根据教材 PDF 自动生成交互式复习页面：左栏 PDF 教材 + 右栏考点笔记，页码链接可跳转、支持缩放搜索。

## 效果预览

![复习页面截图](image.png)

*（示例：深度学习期末复习，教材为《动手学深度学习》(D2L)）*

## 功能特性

- **左右分栏**：左侧 PDF 教材，右侧考点笔记，可拖拽调整宽度
- **页码跳转**：点击笔记中的页码链接（如 `p105`），PDF 自动跳转到对应页
- **缩放控制**：+/- 按钮 或 Ctrl+滚轮 缩放（步长 0.1）
- **键盘快捷键**：← → 翻页，+/- 缩放
- **笔记搜索**：实时搜索高亮笔记内容
- **公式渲染**：KaTeX 渲染 LaTeX 公式
- **响应式**：移动端自动上下排列

## 使用方法

### 1. 准备

```
your-project/
├── 教材.pdf              # 你的 PDF 教材（必需）
├── 复习笔记_考点版.md     # 考点笔记（可让 AI 生成）
└── generate_review_page.py  # 本仓库的生成脚本
```

### 2. 配置脚本

编辑 `generate_review_page.py`，修改顶部两个配置项：

```python
PDF_FILENAME = "你的教材.pdf"     # 替换为实际 PDF 文件名
PAGE_OFFSET = 18                   # 印刷页码 → PDF 页码的偏移量
```

> **如何确定偏移量？** 在 PDF 正文中找到印刷第 1 页，看它在 PDF 中是第几页。例如正文第 1 页 = PDF 第 19 页，则 offset = 18。

### 3. 生成 HTML

```bash
pip install markdown
python3 generate_review_page.py
```

### 4. 启动查看

```bash
python3 -m http.server 8080
```

浏览器打开 `http://localhost:8080/复习笔记_考点版.html`

> ⚠️ 浏览器安全策略限制 file:// 协议加载 PDF。请使用 HTTP 服务器或用 Firefox 打开。

## 考点笔记格式

`复习笔记_考点版.md` 使用 markdown 表格组织，每条考点包含：

| 项目 | 内容 |
|------|------|
| **核心内容** | 公式、定义、概念（LaTeX `$...$`） |
| **对应教材** | 章节与印刷页码，如 `§3.4 p105-p111` |
| **常见考法** | 题型标注：🅰选择/🅱简答/🅲代码 |
| **💡 记忆点** | 口诀、对比、类比 |

> 脚本会自动将 `p数字` 格式的页码转为可点击的 PDF 跳转链接。

## 示例

本仓库的示例基于《动手学深度学习 (PyTorch第二版)》([D2L 开源书籍](https://d2l.ai))，包含：
- `复习笔记_考点版.md` — 35 个考点的深度学习复习笔记
- `generate_review_page.py` — 生成脚本
- `动手学深度学习-PyTorch(第二版).pdf` — 教材 PDF

## Claude Code Skill 自动生成

本工具的工作流已封装为 Claude Code 的 `exam-review` skill：

```bash
# 在项目目录中运行 Claude Code
/exam-review ./教材.pdf
```

skill 会自动完成：
1. 分析 PDF 结构（目录、章节、页码偏移）
2. 与你确认考点范围
3. 生成考点笔记 `复习笔记_考点版.md`
4. 生成 HTML 复习页面 `复习笔记_考点版.html`
5. 启动 HTTP 服务器

一行命令，直接从 PDF 到交互式复习页面。
