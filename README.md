# 深度学习期末复习笔记

根据《动手学深度学习 (PyTorch第二版)》整理的考点复习材料，包含交互式 HTML 复习页面。

## 效果预览

![复习页面截图](image.png)

*左栏为 PDF 教材（支持翻页/缩放），右栏为考点笔记（支持搜索），中间分隔条可拖拽调整宽度*

## 文件说明

| 文件 | 说明 |
|------|------|
| `复习笔记_考点版.md` | 考点版复习笔记，按 35 个考点组织，含记忆点 |
| `generate_review_page.py` | HTML 生成脚本，生成左右分栏的交互式复习页面 |
| `复习笔记_考点版.html` | 生成的 HTML 复习页面（左 PDF 右笔记） |
| `动手学深度学习-PyTorch(第二版).pdf` | 教材 PDF（D2L 开源书籍，[官方地址](https://d2l.ai)） |

## 功能特性

- **左右分栏**：左侧 PDF 教材，右侧考点笔记
- **页码跳转**：点击笔记中的蓝色页码链接（如 `p105`），PDF 自动跳转到对应页
- **缩放控制**：+/- 按钮 或 Ctrl+滚轮 缩放
- **键盘快捷键**：← → 翻页，+/- 缩放
- **拖拽调整**：中间分隔条可拖拽调整左右面板宽度
- **笔记搜索**：顶部搜索框可检索笔记内容
- **公式渲染**：KaTeX 渲染 LaTeX 公式

## 使用方法

### 前提

需要教材 PDF 放在同目录下（已包含本仓库中）。

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

## 考点结构

笔记按 **8 大模块、35 个考点** 组织：

| 模块 | 考点数 | 内容 |
|------|--------|------|
| 基础&nbsp;(§2-4) | 7 | 数据操作、线性回归、Softmax、MLP、过拟合、权重衰退、Dropout |
| CNN&nbsp;(§5-7) | 4 | LeNet、AlexNet、VGG、NiN、GoogLeNet、ResNet、批归一化 |
| 循环神经网络&nbsp;(§8-9) | 6 | RNN、GRU、LSTM、Seq2Seq、语言模型 |
| 注意力机制&nbsp;(§10) | 4 | Attention、Transformer、BERT |
| 优化算法&nbsp;(§11) | 3 | SGD、动量、Adam |
| 计算机视觉&nbsp;(§13) | 5 | 图像增广、微调、R-CNN系列、YOLO、FCN |
| NLP应用&nbsp;(§9,15) | 3 | 机器翻译、NLI、BERT微调 |
| 性能&nbsp;(§12) | 3 | CPU/GPU、多GPU、分布式 |

每个考点包含：**核心内容**（关键公式/概念）、**对应教材页码**、**常见考法**（选择/简答/代码）、**💡记忆点**。

## 技能复用

本项目的工作流已封装为 Claude Code skill：

```bash
# 在 Claude Code 中
/exam-review /path/to/textbook.pdf
```

skill 会自动完成：PDF 分析 → 考点整理 → HTML 生成 → 启动服务器。
