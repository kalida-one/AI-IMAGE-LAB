<template>
  <div class="panel-container">
    <!-- 模型加载状态 -->
    <div v-if="modelStatus !== 'ready'" class="status-bar" :class="modelStatus">
      <div class="status-indicator"></div>
      <span>{{ modelStatusText }}</span>
    </div>

    <!-- 上传区域 -->
    <div class="upload-section">
      <div 
        class="upload-zone"
        :class="{ 'has-file': originalImage }"
        @dragover.prevent
        @drop.prevent="handleDrop"
        @click="triggerUpload"
      >
        <input 
          ref="fileInput"
          type="file" 
          accept="image/*" 
          style="display: none"
          @change="handleFileChange"
        >
        <div v-if="!originalImage" class="upload-placeholder">
          <div class="upload-icon-wrapper">
            <el-icon size="48" color="var(--primary)"><Upload /></el-icon>
          </div>
          <h4>拖拽图片到此处</h4>
          <p>或点击选择文件</p>
          <div class="file-types">
            <span class="file-type">JPG</span>
            <span class="file-type">PNG</span>
          </div>
        </div>
        <div v-else class="preview-container">
          <img :src="originalImage" alt="预览" />
          <div class="preview-overlay">
            <el-icon size="24"><RefreshRight /></el-icon>
            <span>更换图片</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 参数设置 -->
    <div v-if="originalImage" class="settings-section">
      <div class="setting-card">
        <div class="setting-header">
          <el-icon><Setting /></el-icon>
          <span>参数配置</span>
        </div>
        <div class="setting-body">
          <div class="setting-item">
            <label>下采样比例</label>
            <div class="slider-wrapper">
              <input 
                type="range" 
                v-model="downsampleRatio" 
                min="0.1" 
                max="1" 
                step="0.05"
                class="tech-slider"
              >
              <span class="slider-value">{{ downsampleRatio }}</span>
            </div>
          </div>
        </div>
      </div>

      <button 
        class="process-btn"
        :disabled="isProcessing || modelStatus !== 'ready'"
        @click="processImage"
      >
        <span v-if="isProcessing" class="btn-loading"></span>
        <el-icon v-else><Magic /></el-icon>
        <span>{{ isProcessing ? '处理中...' : '开始抠图' }}</span>
      </button>
    </div>

    <!-- 结果对比 -->
    <div v-if="originalImage" class="result-section">
      <div class="result-grid">
        <div class="result-card">
          <div class="result-header">
            <span class="result-title">原始图片</span>
            <div class="result-line"></div>
          </div>
          <div class="result-image">
            <img :src="originalImage" alt="原始" />
          </div>
        </div>

        <div class="result-card">
          <div class="result-header">
            <span class="result-title">抠图结果</span>
            <div class="result-line"></div>
          </div>
          <div class="result-image" :class="{ 'has-result': resultImage }">
            <img v-if="resultImage" :src="resultImage" alt="结果" />
            <div v-else class="waiting-placeholder">
              <el-icon size="32" color="var(--text-secondary)"><Picture /></el-icon>
              <span>等待处理</span>
            </div>
          </div>
          <button v-if="resultImage" class="download-btn" @click="downloadResult">
            <el-icon><Download /></el-icon>
            <span>下载 PNG</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import * as ort from 'onnxruntime-web'

const modelStatus = ref('loading')
const originalImage = ref(null)
const resultImage = ref(null)
const isProcessing = ref(false)
const downsampleRatio = ref(0.25)
const fileInput = ref(null)

let session = null

// 暴露session供父组件释放
const ortSession = computed(() => session)
const modelLoaded = computed(() => modelStatus.value === 'ready')

defineExpose({
  ortSession,
  modelLoaded
})

const modelStatusText = computed(() => {
  switch (modelStatus.value) {
    case 'loading': return '正在加载模型...'
    case 'error': return '模型加载失败'
    default: return ''
  }
})

onMounted(async () => {
  try {
    session = await ort.InferenceSession.create('/models/rvm_resnet50_fp32.onnx')
    modelStatus.value = 'ready'
    ElMessage.success('抠图模型加载成功')
  } catch (error) {
    console.error('模型加载失败:', error)
    modelStatus.value = 'error'
    ElMessage.error('模型加载失败')
  }
})

onUnmounted(async () => {
  if (session) {
    await session.release()
    session = null
  }
})

const triggerUpload = () => {
  fileInput.value?.click()
}

const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (file) loadFile(file)
}

const handleDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    loadFile(file)
  }
}

const loadFile = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    originalImage.value = e.target.result
    resultImage.value = null
  }
  reader.readAsDataURL(file)
}

const preprocessImage = async (imageSrc) => {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const maxSize = 1920
      let width = img.width
      let height = img.height
      
      if (width > maxSize || height > maxSize) {
        if (width > height) {
          height = Math.round((height * maxSize) / width)
          width = maxSize
        } else {
          width = Math.round((width * maxSize) / height)
          height = maxSize
        }
      }
      
      canvas.width = width
      canvas.height = height
      const ctx = canvas.getContext('2d')
      ctx.drawImage(img, 0, 0, width, height)
      
      const imageData = ctx.getImageData(0, 0, width, height)
      const data = imageData.data
      
      const float32Data = new Float32Array(1 * 3 * height * width)
      for (let i = 0; i < height * width; i++) {
        float32Data[i] = data[i * 4] / 255.0
        float32Data[i + height * width] = data[i * 4 + 1] / 255.0
        float32Data[i + 2 * height * width] = data[i * 4 + 2] / 255.0
      }
      
      resolve({ data: float32Data, width, height })
    }
    img.src = imageSrc
  })
}

const processImage = async () => {
  if (!originalImage.value || !session) return
  
  isProcessing.value = true
  
  try {
    const { data, width, height } = await preprocessImage(originalImage.value)
    
    const inputTensor = new ort.Tensor('float32', data, [1, 3, height, width])
    const recTensor = new ort.Tensor('float32', new Float32Array(1 * 1 * 1 * 1).fill(0), [1, 1, 1, 1])
    const downsampleTensor = new ort.Tensor('float32', new Float32Array([downsampleRatio.value]), [1])
    
    const results = await session.run({
      src: inputTensor,
      r1i: recTensor,
      r2i: recTensor,
      r3i: recTensor,
      r4i: recTensor,
      downsample_ratio: downsampleTensor
    })
    
    const fgr = results.fgr.data
    const pha = results.pha.data
    
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    const imageData = ctx.createImageData(width, height)
    
    for (let i = 0; i < width * height; i++) {
      imageData.data[i * 4] = Math.round(fgr[i] * 255)
      imageData.data[i * 4 + 1] = Math.round(fgr[i + width * height] * 255)
      imageData.data[i * 4 + 2] = Math.round(fgr[i + 2 * width * height] * 255)
      imageData.data[i * 4 + 3] = Math.round(pha[i] * 255)
    }
    
    ctx.putImageData(imageData, 0, 0)
    resultImage.value = canvas.toDataURL('image/png')
    
    ElMessage.success('抠图完成')
  } catch (error) {
    console.error('处理失败:', error)
    ElMessage.error('处理失败')
  } finally {
    isProcessing.value = false
  }
}

const downloadResult = () => {
  if (!resultImage.value) return
  const link = document.createElement('a')
  link.download = 'matting-result.png'
  link.href = resultImage.value
  link.click()
}
</script>

<style scoped>
.panel-container {
  color: var(--text-primary);
}

/* 状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid var(--border-glow);
  border-radius: 12px;
  margin-bottom: 20px;
  font-size: 0.9rem;
}

.status-bar.error {
  background: rgba(255, 0, 100, 0.1);
  border-color: rgba(255, 0, 100, 0.3);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
  animation: blink 1s ease-in-out infinite;
}

.status-bar.error .status-indicator {
  background: #ff0064;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* 上传区域 */
.upload-section {
  margin-bottom: 25px;
}

.upload-zone {
  position: relative;
  border: 2px dashed rgba(0, 240, 255, 0.3);
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: rgba(0, 240, 255, 0.02);
}

.upload-zone:hover {
  border-color: var(--primary);
  background: rgba(0, 240, 255, 0.05);
}

.upload-zone.has-file {
  padding: 20px;
}

.upload-icon-wrapper {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 240, 255, 0.1);
  border-radius: 20px;
}

.upload-placeholder h4 {
  font-size: 1.2rem;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.upload-placeholder p {
  color: var(--text-secondary);
  margin-bottom: 15px;
}

.file-types {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.file-type {
  padding: 4px 12px;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.2);
  border-radius: 8px;
  font-size: 0.75rem;
  color: var(--primary);
}

.preview-container {
  position: relative;
}

.preview-container img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 12px;
}

.preview-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 12px;
  opacity: 0;
  transition: opacity 0.3s;
}

.preview-container:hover .preview-overlay {
  opacity: 1;
}

.preview-overlay span {
  margin-top: 8px;
  color: var(--text-primary);
}

/* 设置区域 */
.settings-section {
  margin-bottom: 25px;
}

.setting-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
}

.setting-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  color: var(--primary);
  font-weight: 500;
}

.setting-item label {
  display: block;
  margin-bottom: 10px;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 15px;
}

.tech-slider {
  flex: 1;
  -webkit-appearance: none;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  outline: none;
}

.tech-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
}

.slider-value {
  min-width: 40px;
  text-align: center;
  color: var(--primary);
  font-weight: 600;
}

/* 处理按钮 */
.process-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.3s;
}

.process-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(0, 240, 255, 0.3);
}

.process-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-loading {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 结果区域 */
.result-section {
  margin-top: 30px;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.result-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.result-title {
  font-weight: 600;
  color: var(--text-primary);
}

.result-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, rgba(0, 240, 255, 0.3), transparent);
}

.result-image {
  background: repeating-conic-gradient(#1a1a2e 0% 25%, #16162a 0% 50%) 50% / 20px 20px;
  border-radius: 12px;
  overflow: hidden;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-image img {
  max-width: 100%;
  display: block;
}

.waiting-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
}

.download-btn {
  width: 100%;
  margin-top: 15px;
  padding: 12px;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid var(--border-glow);
  border-radius: 10px;
  color: var(--primary);
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s;
}

.download-btn:hover {
  background: rgba(0, 240, 255, 0.2);
}

@media (max-width: 768px) {
  .upload-zone {
    padding: 30px 20px;
  }
  
  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
