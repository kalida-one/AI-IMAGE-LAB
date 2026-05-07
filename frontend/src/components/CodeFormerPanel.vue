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
          <h4>拖拽老照片到此处</h4>
          <p>或点击选择文件</p>
          <div class="file-types">
            <span class="file-type">JPG</span>
            <span class="file-type">PNG</span>
            <span class="file-type">WebP</span>
          </div>
          <div class="size-hint">
            <el-icon><InfoFilled /></el-icon>
            建议上传包含人脸的老照片，自动修复模糊、划痕、褪色等问题
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
          <el-icon><InfoFilled /></el-icon>
          <span>模型信息</span>
        </div>
        <div class="setting-body">
          <div class="info-row">
            <span class="info-label">模型</span>
            <span class="info-value highlight">CodeFormer INT8</span>
          </div>
          <div class="info-row">
            <span class="info-label">模型大小</span>
            <span class="info-value">92 MB</span>
          </div>
          <div class="info-row">
            <span class="info-label">输入尺寸</span>
            <span class="info-value">{{ originalWidth }} × {{ originalHeight }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">推理尺寸</span>
            <span class="info-value">512 × 512</span>
          </div>
        </div>
      </div>

      <!-- 保真度权重滑块 -->
      <div class="setting-card">
        <div class="setting-header">
          <el-icon><Setting /></el-icon>
          <span>修复参数</span>
        </div>
        <div class="setting-body">
          <div class="slider-row">
            <span class="slider-label">保真度权重</span>
            <span class="slider-value">{{ fidelityWeight.toFixed(1) }}</span>
          </div>
          <input 
            type="range" 
            min="0" 
            max="1" 
            step="0.1" 
            v-model.number="fidelityWeight"
            class="slider"
          />
          <div class="slider-hint">
            <span>高质量</span>
            <span>高保真</span>
          </div>
        </div>
      </div>

      <!-- 进度条 -->
      <div v-if="isProcessing" class="progress-section">
        <div class="progress-header">
          <span>处理进度</span>
          <span class="progress-text">{{ progressPercent }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <div class="progress-detail">{{ progressDetail }}</div>
      </div>

      <button 
        class="process-btn"
        :disabled="isProcessing || modelStatus !== 'ready'"
        @click="processRestoration"
      >
        <span v-if="isProcessing" class="btn-loading"></span>
        <el-icon v-else><MagicStick /></el-icon>
        <span>{{ isProcessing ? '修复中...' : '开始修复' }}</span>
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
            <span class="result-title">修复结果</span>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as ort from 'onnxruntime-web'

const MODEL_INPUT_SIZE = 512
const MODEL_URL = '/models/codeformer_fp16_float.onnx'

const modelStatus = ref('loading')
const originalImage = ref(null)
const resultImage = ref(null)
const isProcessing = ref(false)
const originalWidth = ref(0)
const originalHeight = ref(0)
const fileInput = ref(null)
const progressPercent = ref(0)
const progressDetail = ref('')
const fidelityWeight = ref(0.7)

let ortSession = null

const modelStatusText = computed(() => {
  switch (modelStatus.value) {
    case 'loading': return '正在加载 CodeFormer INT8 模型 (92MB)...'
    case 'error': return '模型加载失败'
    default: return ''
  }
})

import { computed } from 'vue'
import { Upload, InfoFilled, RefreshRight, Setting, MagicStick, Picture, Download } from '@element-plus/icons-vue'

// ==================== 工具函数 ====================

const forceUIUpdate = () => new Promise(resolve => {
  requestAnimationFrame(() => { requestAnimationFrame(() => { resolve() }) })
})

const yieldToMain = () => new Promise(resolve => setTimeout(resolve, 0))

// ==================== 模型加载 ====================

const loadModel = async () => {
  modelStatus.value = 'loading'
  try {
    if (ortSession) {
      await ortSession.release()
      ortSession = null
    }
    ortSession = await ort.InferenceSession.create(MODEL_URL, {
      executionProviders: ['wasm'],
      graphOptimizationLevel: 'all',
      executionMode: 'sequential'
    })
    modelStatus.value = 'ready'
    ElMessage.success('CodeFormer INT8 模型加载成功')
  } catch (error) {
    console.error('模型加载失败:', error)
    modelStatus.value = 'error'
    ElMessage.error('模型加载失败')
  }
}

onMounted(() => { loadModel() })

onUnmounted(async () => {
  if (ortSession) {
    await ortSession.release()
    ortSession = null
  }
})

// ==================== 文件处理 ====================

const triggerUpload = () => { fileInput.value?.click() }

const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (file) loadFile(file)
}

const handleDrop = (e) => {
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) loadFile(file)
}

const loadFile = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    const img = new Image()
    img.onload = () => {
      originalWidth.value = img.width
      originalHeight.value = img.height
    }
    img.src = e.target.result
    originalImage.value = e.target.result
    resultImage.value = null
  }
  reader.readAsDataURL(file)
}

const downloadResult = () => {
  if (!resultImage.value) return
  const link = document.createElement('a')
  link.download = 'restored_' + Date.now() + '.png'
  link.href = resultImage.value
  link.click()
}

// ==================== 核心推理 ====================

const processRestoration = async () => {
  if (!originalImage.value || !ortSession || modelStatus.value !== 'ready') return

  isProcessing.value = true
  progressPercent.value = 0
  progressDetail.value = '准备中...'

  try {
    const img = await new Promise((resolve, reject) => {
      const i = new Image()
      i.onload = () => resolve(i)
      i.onerror = reject
      i.src = originalImage.value
    })

    const origW = img.naturalWidth
    const origH = img.naturalHeight
    const S = MODEL_INPUT_SIZE

    // 1. 预处理：读取图像并resize到512x512，归一化到[-1, 1]
    progressPercent.value = 10
    progressDetail.value = '预处理图像...'
    await forceUIUpdate()

    const canvas = document.createElement('canvas')
    canvas.width = S
    canvas.height = S
    const ctx = canvas.getContext('2d')
    ctx.drawImage(img, 0, 0, S, S)
    const imgData = ctx.getImageData(0, 0, S, S)

    // 转换为tensor [1, 3, 512, 512]，归一化到[-1, 1]
    const inputData = new Float32Array(1 * 3 * S * S)
    for (let y = 0; y < S; y++) {
      for (let x = 0; x < S; x++) {
        const idx = (y * S + x) * 4
        const r = imgData.data[idx] / 255.0
        const g = imgData.data[idx + 1] / 255.0
        const b = imgData.data[idx + 2] / 255.0
        
        // 归一化到[-1, 1]: (x - 0.5) / 0.5 = 2x - 1
        const pos = y * S + x
        inputData[0 * S * S + pos] = r * 2 - 1  // R
        inputData[1 * S * S + pos] = g * 2 - 1  // G
        inputData[2 * S * S + pos] = b * 2 - 1  // B
      }
      if (y % 10 === 0) await yieldToMain()
    }

    // 2. 推理
    progressPercent.value = 30
    progressDetail.value = 'CodeFormer神经网络推理中...'
    await forceUIUpdate()

    const tensorX = new ort.Tensor('float32', inputData, [1, 3, S, S])
    const tensorW = new ort.Tensor('float32', new Float32Array([fidelityWeight.value]), [1])

    const feeds = {
      'x': tensorX,
      'w': tensorW
    }
    
    const results = await ortSession.run(feeds)
    const outputY = results['y']
    const outData = outputY.data

    // 3. 后处理：动态归一化到[0, 255]
    progressPercent.value = 80
    progressDetail.value = '生成修复图像...'
    await forceUIUpdate()

    // 第一遍扫描：找出实际输出范围，用真实范围做归一化，避免硬截断色块
    let vMin = Infinity, vMax = -Infinity
    const totalPixels = 3 * S * S
    for (let i = 0; i < totalPixels; i++) {
      const v = outData[i]
      if (v < vMin) vMin = v
      if (v > vMax) vMax = v
    }
    // 留1%余量防止极端值
    const range = vMax - vMin
    const normMin = vMin - range * 0.01
    const normMax = vMax + range * 0.01
    const normRange = normMax - normMin

    const outCanvas = document.createElement('canvas')
    outCanvas.width = S
    outCanvas.height = S
    const outCtx = outCanvas.getContext('2d')
    const outImgData = outCtx.createImageData(S, S)

    for (let y = 0; y < S; y++) {
      for (let x = 0; x < S; x++) {
        const pos = y * S + x
        // 动态归一化: (val - normMin) / normRange * 255，零截断
        const r = Math.max(0, Math.min(255, Math.round((outData[0 * S * S + pos] - normMin) / normRange * 255)))
        const g = Math.max(0, Math.min(255, Math.round((outData[1 * S * S + pos] - normMin) / normRange * 255)))
        const b = Math.max(0, Math.min(255, Math.round((outData[2 * S * S + pos] - normMin) / normRange * 255)))
        
        const idx = pos * 4
        outImgData.data[idx] = r
        outImgData.data[idx + 1] = g
        outImgData.data[idx + 2] = b
        outImgData.data[idx + 3] = 255
      }
      if (y % 10 === 0) await yieldToMain()
    }

    outCtx.putImageData(outImgData, 0, 0)
    
    // 如果原始尺寸不是512x512，resize回去
    if (origW !== S || origH !== S) {
      progressDetail.value = '调整图像尺寸...'
      const finalCanvas = document.createElement('canvas')
      finalCanvas.width = origW
      finalCanvas.height = origH
      const finalCtx = finalCanvas.getContext('2d')
      finalCtx.drawImage(outCanvas, 0, 0, origW, origH)
      resultImage.value = finalCanvas.toDataURL('image/png')
    } else {
      resultImage.value = outCanvas.toDataURL('image/png')
    }

    progressPercent.value = 100
    progressDetail.value = '完成！'
    ElMessage.success('老照片修复完成！')
    
  } catch (error) {
    console.error('处理失败:', error)
    ElMessage.error('处理失败: ' + error.message)
  } finally {
    isProcessing.value = false
  }
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
  margin-bottom: 15px;
}

.file-type {
  padding: 4px 12px;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.2);
  border-radius: 8px;
  font-size: 0.75rem;
  color: var(--primary);
}

.size-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 0.85rem;
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
  margin-bottom: 15px;
}

.setting-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 15px;
  color: var(--primary);
  font-weight: 500;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.info-value {
  font-weight: 600;
  color: var(--text-primary);
}

.info-value.highlight {
  color: var(--primary);
}

/* 滑块 */
.slider-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.slider-label {
  color: var(--text-secondary);
}

.slider-value {
  color: var(--primary);
  font-weight: 600;
}

.slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
}

.slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.slider-hint {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

/* 进度条 */
.progress-section {
  margin-bottom: 20px;
  padding: 20px;
  background: rgba(0, 240, 255, 0.05);
  border: 1px solid var(--border-glow);
  border-radius: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 0.9rem;
}

.progress-text {
  color: var(--primary);
  font-weight: 600;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  border-radius: 4px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
}

.progress-detail {
  margin-top: 8px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  text-align: center;
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
