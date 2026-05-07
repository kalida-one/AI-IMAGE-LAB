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
          <h4>拖拽黑白照片到此处</h4>
          <p>或点击选择文件</p>
          <div class="file-types">
            <span class="file-type">JPG</span>
            <span class="file-type">PNG</span>
            <span class="file-type">WebP</span>
          </div>
          <div class="size-hint">
            <el-icon><InfoFilled /></el-icon>
            建议上传黑白/灰度照片，自动恢复自然色彩
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
            <span class="info-value highlight">DDColor-Tiny INT8</span>
          </div>
          <div class="info-row">
            <span class="info-label">模型大小</span>
            <span class="info-value">54 MB</span>
          </div>
          <div class="info-row">
            <span class="info-label">输入尺寸</span>
            <span class="info-value">{{ originalWidth }} × {{ originalHeight }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">推理尺寸</span>
            <span class="info-value">256 × 256</span>
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
        @click="processColorization"
      >
        <span v-if="isProcessing" class="btn-loading"></span>
        <el-icon v-else><Brush /></el-icon>
        <span>{{ isProcessing ? '处理中...' : '开始上色' }}</span>
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
            <span class="result-title">上色结果</span>
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
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import * as ort from 'onnxruntime-web'

const MODEL_INPUT_SIZE = 256
const MODEL_URL = '/models/ddcolor_tiny_int8.onnx'

const modelStatus = ref('loading')
const originalImage = ref(null)
const resultImage = ref(null)
const isProcessing = ref(false)
const originalWidth = ref(0)
const originalHeight = ref(0)
const fileInput = ref(null)
const progressPercent = ref(0)
const progressDetail = ref('')

let ortSession = null

const modelLoaded = computed(() => modelStatus.value === 'ready')

defineExpose({
  get ortSession() { return ortSession },
  get modelLoaded() { return modelLoaded.value },
  set modelLoaded(v) { if (!v) modelStatus.value = 'loading' }
})

const modelStatusText = computed(() => {
  switch (modelStatus.value) {
    case 'loading': return '正在加载 DDColor-Tiny INT8 模型 (54MB)...'
    case 'error': return '模型加载失败'
    default: return ''
  }
})

// ==================== LAB色彩空间转换 ====================

function srgbToLinear(c) {
  c = c / 255.0
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
}

function linearToSrgb(c) {
  c = Math.max(0, Math.min(1, c))
  return c <= 0.0031308 ? c * 12.92 : 1.055 * Math.pow(c, 1 / 2.4) - 0.055
}

function rgbToXyz(r, g, b) {
  const rl = srgbToLinear(r), gl = srgbToLinear(g), bl = srgbToLinear(b)
  return [
    0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl,
    0.2126729 * rl + 0.7151522 * gl + 0.0721750 * bl,
    0.0193339 * rl + 0.1191920 * gl + 0.9503041 * bl
  ]
}

function xyzToRgb(x, y, z) {
  const rl =  3.2404542 * x - 1.5371385 * y - 0.4985314 * z
  const gl = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
  const bl =  0.0556434 * x - 0.2040259 * y + 1.0572252 * z
  return [
    Math.round(linearToSrgb(rl) * 255),
    Math.round(linearToSrgb(gl) * 255),
    Math.round(linearToSrgb(bl) * 255)
  ]
}

function xyzToLab(x, y, z) {
  const xn = 0.95047, yn = 1.0, zn = 1.08883
  const fx = x / xn > 0.008856 ? Math.pow(x / xn, 1/3) : 7.787 * x / xn + 16/116
  const fy = y / yn > 0.008856 ? Math.pow(y / yn, 1/3) : 7.787 * y / yn + 16/116
  const fz = z / zn > 0.008856 ? Math.pow(z / zn, 1/3) : 7.787 * z / zn + 16/116
  return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)]
}

function labToXyz(L, a, b) {
  const fy = (L + 16) / 116
  const fx = a / 500 + fy
  const fz = fy - b / 200
  const xn = 0.95047, yn = 1.0, zn = 1.08883
  const x = fx > 0.206897 ? fx * fx * fx : (fx - 16/116) / 7.787
  const y = fy > 0.206897 ? fy * fy * fy : (fy - 16/116) / 7.787
  const z = fz > 0.206897 ? fz * fz * fz : (fz - 16/116) / 7.787
  return [x * xn, y * yn, z * zn]
}

function rgbToLab(r, g, b) { return xyzToLab(...rgbToXyz(r, g, b)) }
function labToRgb(L, a, b) { return xyzToRgb(...labToXyz(L, a, b)) }

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
    ElMessage.success('DDColor-Tiny INT8 模型加载成功')
  } catch (error) {
    console.error('模型加载失败:', error)
    modelStatus.value = 'error'
    ElMessage.error('模型加载失败')
  }
}

onMounted(() => { loadModel() })

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
  link.download = 'colorized_' + Date.now() + '.png'
  link.href = resultImage.value
  link.click()
}

// ==================== 核心推理 ====================

const processColorization = async () => {
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

    // 1. 提取原始L通道
    progressPercent.value = 10
    progressDetail.value = '提取亮度通道...'
    await forceUIUpdate()

    const canvasOrig = document.createElement('canvas')
    canvasOrig.width = origW
    canvasOrig.height = origH
    const ctxOrig = canvasOrig.getContext('2d')
    ctxOrig.drawImage(img, 0, 0)
    const origData = ctxOrig.getImageData(0, 0, origW, origH)

    const origL = new Float32Array(origW * origH)
    for (let i = 0; i < origW * origH; i++) {
      const idx = i * 4
      const [L] = rgbToLab(origData.data[idx], origData.data[idx+1], origData.data[idx+2])
      origL[i] = L
    }

    // 2. 构造灰度LAB -> RGB 输入
    progressPercent.value = 25
    progressDetail.value = '预处理灰度图像...'
    await forceUIUpdate()

    const canvasResize = document.createElement('canvas')
    canvasResize.width = S
    canvasResize.height = S
    const ctxResize = canvasResize.getContext('2d')
    ctxResize.drawImage(img, 0, 0, S, S)
    const resizedData = ctxResize.getImageData(0, 0, S, S)

    const inputData = new Float32Array(1 * 3 * S * S)
    for (let y = 0; y < S; y++) {
      for (let x = 0; x < S; x++) {
        const idx = (y * S + x) * 4
        const [L] = rgbToLab(resizedData.data[idx], resizedData.data[idx+1], resizedData.data[idx+2])
        const [rr, rg, rb] = labToRgb(L, 0, 0)
        const pos = y * S + x
        inputData[0 * S * S + pos] = rr / 255.0
        inputData[1 * S * S + pos] = rg / 255.0
        inputData[2 * S * S + pos] = rb / 255.0
      }
      if (y % 10 === 0) await yieldToMain()
    }

    // 3. 推理
    progressPercent.value = 40
    progressDetail.value = '神经网络推理中...'
    await forceUIUpdate()

    const tensor = new ort.Tensor('float32', inputData, [1, 3, S, S])
    const feeds = {}
    feeds[ortSession.inputNames[0]] = tensor
    const results = await ortSession.run(feeds)
    const outputTensor = results[ortSession.outputNames[0]]
    const outData = outputTensor.data

    // 4. 双线性插值放大AB通道
    progressPercent.value = 75
    progressDetail.value = '色彩合成中...'
    await forceUIUpdate()

    const abA = new Float32Array(origW * origH)
    const abB = new Float32Array(origW * origH)

    for (let oy = 0; oy < origH; oy++) {
      for (let ox = 0; ox < origW; ox++) {
        const sx = ox * (S - 1) / (origW - 1)
        const sy = oy * (S - 1) / (origH - 1)
        const x0 = Math.floor(sx), y0 = Math.floor(sy)
        const x1 = Math.min(x0 + 1, S - 1), y1 = Math.min(y0 + 1, S - 1)
        const fx = sx - x0, fy = sy - y0

        abA[oy * origW + ox] = outData[0*S*S+y0*S+x0]*(1-fx)*(1-fy) + outData[0*S*S+y0*S+x1]*fx*(1-fy) + outData[0*S*S+y1*S+x0]*(1-fx)*fy + outData[0*S*S+y1*S+x1]*fx*fy
        abB[oy * origW + ox] = outData[1*S*S+y0*S+x0]*(1-fx)*(1-fy) + outData[1*S*S+y0*S+x1]*fx*(1-fy) + outData[1*S*S+y1*S+x0]*(1-fx)*fy + outData[1*S*S+y1*S+x1]*fx*fy
      }
      if (oy % 20 === 0) await yieldToMain()
    }

    // 5. LAB -> RGB 输出
    progressPercent.value = 90
    progressDetail.value = '生成彩色图像...'
    await forceUIUpdate()

    const canvas = document.createElement('canvas')
    canvas.width = origW
    canvas.height = origH
    const ctx = canvas.getContext('2d')
    const imageData = ctx.createImageData(origW, origH)

    for (let i = 0; i < origW * origH; i++) {
      const [r, g, b] = labToRgb(origL[i], abA[i], abB[i])
      const idx = i * 4
      imageData.data[idx] = Math.min(255, Math.max(0, r))
      imageData.data[idx + 1] = Math.min(255, Math.max(0, g))
      imageData.data[idx + 2] = Math.min(255, Math.max(0, b))
      imageData.data[idx + 3] = 255
    }

    ctx.putImageData(imageData, 0, 0)
    resultImage.value = canvas.toDataURL('image/png')

    progressPercent.value = 100
    progressDetail.value = '完成！'
    ElMessage.success('上色完成')
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
