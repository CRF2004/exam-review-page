# 深度学习期末复习笔记

根据《动手学深度学习 (PyTorch第二版)》整理的考点复习材料，包含交互式 HTML 复习页面。

## 文件说明

| 文件 | 说明 |
|------|------|
| `复习笔记_考点版.md` | 考点版复习笔记，按 35 个考点组织，含记忆点 |
| `generate_review_page.py` | HTML 生成脚本，生成左右分栏的交互式复习页面 |
| `复习笔记_考点版.html` | 生成的 HTML 复习页面（左 PDF 右笔记） |

## 功能特性

- **左右分栏**：左侧 PDF 教材，右侧考点笔记
- **页码跳转**：点击笔记中的页码链接，PDF 自动跳转到对应页
- **缩放控制**：+/- 按钮 或 Ctrl+滚轮 缩放
- **键盘快捷键**：← → 翻页，+/- 缩放
- **拖拽调整**：中间分隔条可拖拽调整左右面板宽度
- **笔记搜索**：顶部搜索框可检索笔记内容
- **公式渲染**：KaTeX 渲染 LaTeX 公式

## 使用方法

### 前提

需要教材 PDF 文件放在同目录下。

### 生成 HTML

```bash
python3 generate_review_page.py
```

### 启动查看

```bash
python3 -m http.server 8080
```

浏览器打开 `http://localhost:8080/复习笔记_考点版.html`

> ⚠️ 由于浏览器安全策略，直接双击 HTML 文件可能无法加载 PDF。请使用 HTTP 服务器或用 Firefox 打开。

## 技能复用

本项目的工作流已封装为 Claude Code skill，使用方法：

```bash
# 在 Claude Code 中
/exam-review /path/to/textbook.pdf
```

skill 会自动完成：PDF 分析 → 考点整理 → HTML 生成 → 启动服务器。
