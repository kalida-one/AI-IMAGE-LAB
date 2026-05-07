"""
AI IMAGE LAB - Flask后端
用于本地托管前端静态文件和模型文件
"""
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# 配置
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
MODELS_FOLDER = os.path.join(os.path.dirname(__file__), 'models')

# 确保模型目录存在
os.makedirs(MODELS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """首页"""
    return send_from_directory(STATIC_FOLDER, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """静态文件"""
    return send_from_directory(STATIC_FOLDER, path)

@app.route('/models/<path:filename>')
def models(filename):
    """模型文件 - 本地加载"""
    # 支持跨域请求，允许WebAssembly加载模型
    response = send_from_directory(MODELS_FOLDER, filename)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Cross-Origin-Resource-Policy'] = 'cross-origin'
    return response

@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'message': 'AI IMAGE LAB 服务正常运行',
        'mode': 'local'
    })

@app.route('/api/models')
def list_models():
    """列出本地可用模型"""
    models = []
    
    # 模型列表（对应前端实际使用的模型）
    model_files = [
        ('rvm_resnet50_fp32.onnx', '智能抠图', 'matting'),
        ('RealESRGAN_x4plus_anime_6B_merged.onnx', '超分辨率', 'super_resolution'),
        ('ddcolor_tiny_int8.onnx', '黑白上色', 'colorization'),
        ('codeformer_fp16_float.onnx', '老照片修复', 'restoration'),
    ]
    
    for filename, name, type_ in model_files:
        filepath = os.path.join(MODELS_FOLDER, filename)
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            models.append({
                'name': name,
                'filename': filename,
                'type': type_,
                'size_mb': round(size_mb, 2),
                'status': 'available'
            })
        else:
            models.append({
                'name': name,
                'filename': filename,
                'type': type_,
                'size_mb': 0,
                'status': 'missing'
            })
    
    return jsonify({
        'models': models,
        'count': len([m for m in models if m['status'] == 'available']),
        'total_size_mb': round(sum([m['size_mb'] for m in models if m['status'] == 'available']), 2)
    })

if __name__ == '__main__':
    print("=" * 60)
    print("AI IMAGE LAB - Flask后端")
    print("=" * 60)
    print(f"静态文件目录: {STATIC_FOLDER}")
    print(f"模型文件目录: {MODELS_FOLDER}")
    print("-" * 60)
    
    # 检查模型文件
    model_files = [
        'rvm_resnet50_fp32.onnx',
        'RealESRGAN_x4plus_anime_6B_merged.onnx',
        'ddcolor_tiny_int8.onnx',
        'codeformer_fp16_float.onnx',
    ]
    
    for filename in model_files:
        filepath = os.path.join(MODELS_FOLDER, filename)
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"✓ {filename} ({size_mb:.1f} MB)")
        else:
            print(f"✗ {filename} (缺失)")
    
    print("=" * 60)
    print("访问: http://localhost:5005")
    print("=" * 60)
    
    # 开发模式运行
    app.run(
        host='0.0.0.0',
        port=5005,
        debug=True,
        threaded=True
    )
