# AI IMAGE LAB

<p align="center">
  <img src="https://img.shields.io/badge/Vue-3.4+-green.svg" alt="Vue">
  <img src="https://img.shields.io/badge/ONNX-Runtime-blue.svg" alt="ONNX">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

<p align="center">
  <b>纯浏览器端 AI 图像处理工具箱</b>
</p>

<p align="center">
  无需服务器，所有 AI 模型在浏览器本地运行，保护隐私，永久免费
</p>

---

## ✨ 功能特性

| 功能 | 模型 | 大小 | 说明 |
|------|------|------|------|
| 🔥 **智能抠图** | RVM ResNet50 | 107MB | 高精度人像分割，支持透明背景 |
| 🔍 **超分辨率** | Real-ESRGAN 4x | 67MB | 动漫/照片智能放大4倍 |
| 🎨 **黑白上色** | DDColor Tiny | 57MB | 老照片自动上色，NeurIPS 2022 |
| 🖼️ **老照片修复** | CodeFormer | 96MB | 人脸修复，去除模糊划痕 |
| 💬 **AI 对话** | Qwen2.5-0.5B | 488MB | 浏览器本地运行大语言模型 |

---

## 🚀 两种使用方式

本项目提供两种使用方式，根据你的需求选择：

### 方式一：在线体验版（推荐体验）

**适合：** 快速体验、在线分享、无需本地环境

- 零配置，打开浏览器即用
- 图像模型从服务器加载
- LLM 模型自动下载到浏览器缓存
- 首次加载需下载模型，后续自动缓存秒开

**访问地址：**
```
http://www.junchuang.top:5005
```

### 方式二：本地部署版（推荐开发）

**适合：** 本地开发、离线使用、内网部署、二次开发

- 所有模型文件打包在本地，无需联网下载
- 完全离线运行，隐私保护最强
- 启动即用，首次加载无需等待模型下载
- 支持自定义模型路径

**部署方法：**
```bash
# 克隆仓库
git clone https://github.com/kalida-one/ai-image-lab.git
cd ai-image-lab

# 安装 Python 依赖
pip install -r backend/requirements.txt

# 启动服务
cd backend
python app.py
```

访问 http://localhost:5005

> **注意：** 由于模型文件较大，本仓库不包含模型文件。请从网盘下载并解压到 `backend/models/` 目录：
> 
> **模型下载：** [models.zip](https://pan.baidu.com/s/1yYtbyZfwG2OxYrePwGGtlw?pwd=spjp)
> - 提取码: `spjp`
> - 大小: 约 820MB
> - 解压后将 `models/` 目录放入 `backend/` 文件夹下

### 两种版本对比

| 特性 | 在线体验版 | 本地部署版 |
|------|-------------------|-------------|
| **部署难度** | ⭐ 零配置 | ⭐⭐ 需要 Python |
| **网络依赖** | 首次需联网下载模型 | 完全离线 |
| **首次加载** | 需等待模型下载 | 秒开 |
| **隐私保护** | 浏览器本地推理 | 完全离线 |
| **LLM 模型** | 从 hf-mirror.com 自动下载 | 本地已包含 |
| **图像模型** | 从 GitHub 仓库加载 | 本地已包含 |
| **适合场景** | 在线体验/分享 | 本地/内网/开发 |
| **仓库大小** | ~330MB（仅图像模型） | ~820MB（含所有模型） |

---

## 🏗️ 项目结构

```
ai-image-lab/
├── backend/
│   ├── app.py                            # Flask 后端
│   ├── requirements.txt                  # Python 依赖
│   ├── models/                           # 模型文件存放位置
│   │   ├── rvm_resnet50_fp32.onnx        # 抠图 (107MB)
│   │   ├── RealESRGAN_x4plus_anime_6B_merged.onnx  # 超分 (67MB)
│   │   ├── ddcolor_tiny_int8.onnx        # 上色 (57MB)
│   │   ├── codeformer_fp16_float.onnx    # 修复 (96MB)
│   │   └── qwen2.5-0.5b-instruct/       # LLM 模型（含 tokenizer）
│   │       ├── config.json
│   │       ├── tokenizer.json
│   │       └── onnx/model_quantized.onnx  # INT4 量化 (488MB)
│   └── static/                           # 前端构建产物
├── frontend/                             # Vue 3 前端源码
│   ├── src/
│   │   ├── components/                   # 功能组件
│   │   │   ├── MattingPanel.vue          # 抠图
│   │   │   ├── SuperResolutionPanel.vue  # 超分
│   │   │   ├── ColorizationPanel.vue     # 上色
│   │   │   ├── CodeFormerPanel.vue       # 修复
│   │   │   └── ChatPanel.vue             # AI 对话
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── docs/
│   ├── GITHUB_PAGES.md                   # GitHub Pages 部署指南
│   ├── FLASK_DEPLOY.md                   # Flask 部署指南
│   └── wechat-pay.jpg                    # 请作者喝茶
├── LICENSE                               # MIT 开源协议
└── README.md
```

> **模型文件说明：** 所有 AI 模型文件均存放在 `backend/models/` 目录下。如需单独使用图像模型，可从该目录拷贝。由于 GitHub 对大文件的限制，建议使用 Flask 版本进行本地部署，或参考部署文档了解如何配置模型路径。

---

## 🛠️ 技术栈

- **前端**: Vue 3 + Element Plus + Vite
- **AI 推理**: ONNX Runtime Web (WASM) + Transformers.js
- **后端**: Flask (仅用于本地静态文件服务)
- **模型格式**: ONNX，INT8/FP16 量化优化
- **LLM**: Qwen2.5-0.5B-Instruct INT4 量化

---

## 💡 核心亮点

1. **纯浏览器端运行** - 所有 AI 推理在本地完成，图片不上传服务器
2. **模型自动缓存** - 首次下载后自动缓存到浏览器 IndexedDB，后续秒开
3. **内存优化** - 切换功能自动卸载上一个模型，释放内存
4. **量化加速** - INT8/FP16/INT4 量化，模型体积减少 50-75%
5. **国内加速** - LLM 模型使用 hf-mirror.com 国内镜像站

---

## 📋 模型说明

### 图像模型（两种版本均包含）

| 模型 | 大小 | 用途 |
|------|------|------|
| RVM ResNet50 | 107MB | 人像分割抠图 |
| Real-ESRGAN 4x | 67MB | 动漫/照片超分辨率 |
| DDColor Tiny | 57MB | 黑白照片上色 |
| CodeFormer | 96MB | 老照片人脸修复 |

### LLM 模型（Flask 版本地包含，GitHub Pages 版自动下载）

| 模型 | 大小 | 量化 | 用途 |
|------|------|------|------|
| Qwen2.5-0.5B-Instruct | 488MB | INT4 | AI 多轮对话 |

---

## 🙏 请作者喝茶

如果这个项目对你有帮助，可以请作者喝杯茶 ☕

<p align="center">
  <img src="docs/wechat-pay.jpg" width="300" alt="微信收款码">
</p>

---

## 📄 开源协议

MIT License © 2026 AI IMAGE LAB

---

## 🙏 致谢

- [RVM](https://github.com/PeterL1n/RobustVideoMatting) - 人像分割
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) - 超分辨率
- [DDColor](https://github.com/piddnad/DDColor) - 图像上色
- [CodeFormer](https://github.com/sczhou/CodeFormer) - 人脸修复
- [Qwen](https://github.com/QwenLM/Qwen) - 大语言模型
- [ONNX Runtime](https://github.com/microsoft/onnxruntime) - 跨平台推理引擎
- [Transformers.js](https://github.com/xenova/transformers.js) - 浏览器 AI 推理

---

<p align="center">
  Made with ❤️ by AI IMAGE LAB
</p>
