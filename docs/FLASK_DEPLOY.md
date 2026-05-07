# Flask 本地部署指南

## 目录结构

```
backend/
├── app.py              # Flask 主程序
├── requirements.txt    # Python 依赖
├── models/            # 本地模型文件（需自行下载）
│   ├── rvm_resnet50_fp32.onnx
│   ├── RealESRGAN_x4plus_anime_6B_merged.onnx
│   ├── ddcolor_tiny_int8.onnx
│   └── codeformer_fp16_float.onnx
└── static/            # 前端构建文件
```

## 安装步骤

### 1. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 下载模型文件

模型文件需要手动下载到 `backend/models/` 目录：

| 模型 | 下载地址 | 大小 |
|------|----------|------|
| RVM ResNet50 | [GitHub Release](https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_resnet50_fp32.onnx) | 107MB |
| Real-ESRGAN | [HuggingFace](https://huggingface.co/onnx-community/Real-ESRGAN-x4plus-anime-6B/resolve/main/onnx/model.onnx) | 67MB |
| DDColor | [HuggingFace](https://huggingface.co/onnx-community/ddcolor-tiny/resolve/main/onnx/model.onnx) | 57MB |
| CodeFormer | [HuggingFace](https://huggingface.co/onnx-community/CodeFormer/resolve/main/onnx/model.onnx) | 96MB |

> **注意**：模型文件较大，首次下载需要一些时间。

### 3. 准备前端静态文件

```bash
cd frontend
npm install
npm run build
```

构建完成后，将 `backend/static/` 目录下的文件复制到 Flask 的 static 目录。

### 4. 运行 Flask 服务

```bash
cd backend
python app.py
```

访问 http://localhost:5000

## 特点

- ✅ **本地模型加载** - 模型文件从本地 `backend/models/` 加载，无需外部网络
- ✅ **隐私保护** - 所有图像处理在本地完成，不上传云端
- ✅ **快速响应** - 本地模型加载，响应更快
- ⚠️ **需要下载模型** - 首次使用需要下载约 330MB 模型文件

## 与 GitHub Pages 版本的区别

| 特性 | Flask 本地版 | GitHub Pages 版 |
|------|-------------|-----------------|
| 模型来源 | 本地文件 | CDN/HuggingFace |
| 网络依赖 | 仅需首次下载模型 | 每次加载需联网 |
| 隐私保护 | 完全离线 | 依赖外部 CDN |
| 部署难度 | 需要 Python 环境 | 零配置 |
| 适合场景 | 本地开发/私有部署 | 快速体验/分享 |

## API 接口

### 健康检查
```
GET /api/health
```

### 模型列表
```
GET /api/models
```

返回本地可用的模型列表及状态。
