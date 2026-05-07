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
          <div class="size-hint">
            <el-icon><InfoFilled /></el-icon>
            支持任意尺寸，大图自动分片处理
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
          <span>放大配置</span>
        </div>
        <div class="setting-body">
          <div class="info-row">
            <span class="info-label">放大倍数</span>
            <span class="info-value highlight">4x</span>
          </div>
          <div class="info-row">
            <span class="info-label">输入尺寸</span>
            <span class="info-value">{{ originalWidth }} × {{ originalHeight }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">输出尺寸</span>
            <span class="info-value highlight">{{ originalWidth * 4 }} × {{ originalHeight * 4 }}</span>
          </div>
          <div class="info-row" v-if="tileInfo">
            <span class="info-label">分片策略</span>
            <span class="info-value">{{ tileInfo }}</span>
          </div>
        </div>
      </div>

      <div class="setting-card">
        <div class="setting-header">
          <el-icon><Grid /></el-icon>
          <span>分片设置</span>
        </div>
        <div class="setting-body">
          <div class="setting-item">
            <label>分片大小</label>
            <div class="slider-wrapper">
              <input 
                type="range" 
                v-model.number="tileSize" 
                min="64" 
                max="512" 
                step="64"
                class="tech-slider"
              >
              <span class="slider-value">{{ tileSize }}px</span>
            </div>
          </div>
          <div class="setting-item">
            <label>重叠像素</label>
            <div class="slider-wrapper">
              <input 
                type="range" 
                v-model.number="overlap" 
                min="0" 
                max="64" 
                step="8"
                class="tech-slider"
              >
              <span class="slider-value">{{ overlap }}px</span>
            </div>
          </div>
          <div class="setting-hint">
            <el-icon><InfoFilled /></el-icon>
            大图自动切分为小块分别处理，避免浏览器内存溢出。分片越小内存占用越低，但处理速度越慢。
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
        @click="processImage"
      >
        <span v-if="isProcessing" class="btn-loading"></span>
        <el-icon v-else><ZoomIn /></el-icon>
        <span>{{ isProcessing ? '处理中...' : '开始超分辨率' }}</span>
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
            <span class="result-title">超分辨率结果</span>
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
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as ort from 'onnxruntime-web'

const modelStatus = ref('loading')
const originalImage = ref(null)
const resultImage = ref(null)
const isProcessing = ref(false)
const originalWidth = ref(0)
const originalHeight = ref(0)
const fileInput = ref(null)
const tileSize = ref(256)
const overlap = ref(32)
const progressPercent = ref(0)
const progressDetail = ref('')

let session = null
let cancelToken = { cancelled: false }

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

// 计算分片信息
const tileInfo = computed(() => {
  if (!originalWidth.value || !originalHeight.value) return null
  const w = originalWidth.value
  const h = originalHeight.value
  const ts = tileSize.value
  if (w <= ts && h <= ts) return '无需分片（整图处理）'
  const cols = Math.ceil((w - overlap.value) / (ts - overlap.value))
  const rows = Math.ceil((h - overlap.value) / (ts - overlap.value))
  return `${cols}×${rows} = ${cols * rows} 个分片`
})

onMounted(async () => {
  try {
    session = await ort.InferenceSession.create('/models/RealESRGAN_x4plus_anime_6B_merged.onnx')
    modelStatus.value = 'ready'
    ElMessage.success('超分辨率模型加载成功')
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

// 从 canvas 提取 NCHW float32 数据
const canvasToNCHW = (canvas) => {
  const ctx = canvas.getContext('2d')
  const w = canvas.width
  const h = canvas.height
  const imageData = ctx.getImageData(0, 0, w, h)
  const data = imageData.data
  const float32 = new Float32Array(3 * h * w)
  for (let i = 0; i < h * w; i++) {
    float32[i] = data[i * 4] / 255.0
    float32[i + h * w] = data[i * 4 + 1] / 255.0
    float32[i + 2 * h * w] = data[i * 4 + 2] / 255.0
  }
  return float32
}

// NCHW float32 数据写入 canvas
const nchwToCanvas = (float32, width, height) => {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  const imageData = ctx.createImageData(width, height)
  const total = width * height
  for (let i = 0; i < total; i++) {
    imageData.data[i * 4] = Math.max(0, Math.min(255, float32[i] * 255))
    imageData.data[i * 4 + 1] = Math.max(0, Math.min(255, float32[i + total] * 255))
    imageData.data[i * 4 + 2] = Math.max(0, Math.min(255, float32[i + 2 * total] * 255))
    imageData.data[i * 4 + 3] = 255
  }
  ctx.putImageData(imageData, 0, 0)
  return canvas
}

// 运行单次模型推理
const runModel = async (inputData, h, w) => {
  const tensor = new ort.Tensor('float32', inputData, [1, 3, h, w])
  const results = await session.run({ input: tensor })
  return results.output.data
}

// 线性混合两个数组（用于重叠区域融合）
const blendArrays = (arr1, arr2, alpha, length) => {
  const result = new Float32Array(length)
  for (let i = 0; i < length; i++) {
    result[i] = arr1[i] * (1 - alpha) + arr2[i] * alpha
  }
  return result
}

// 分片处理主逻辑
const processTiled = async (srcCanvas) => {
  const srcW = srcCanvas.width
  const srcH = srcCanvas.height
  const ts = tileSize.value
  const ov = overlap.value
  const scale = 4
  const outW = srcW * scale
  const outH = srcH * scale

  // 输出缓冲区
  const outputBuf = new Float32Array(3 * outH * outW)
  // 权重缓冲区（用于重叠区域加权平均）
  const weightBuf = new Float32Array(outH * outW)

  // 计算分片步长和数量
  const step = Math.max(ts - ov, 1)
  const cols = Math.ceil((srcW - ov) / step)
  const rows = Math.ceil((srcH - ov) / step)
  const totalTiles = cols * rows

  let processedTiles = 0

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      if (cancelToken.cancelled) return null

      // 计算源图分片区域
      let sx = col * step
      let sy = row * step
      let sw = Math.min(ts, srcW - sx)
      let sh = Math.min(ts, srcH - sy)

      // 如果不是最后一个分片，强制使用 tileSize
      if (col < cols - 1) sw = ts
      if (row < rows - 1) sh = ts

      // 边界修正
      sx = Math.max(0, Math.min(sx, srcW - 1))
      sy = Math.max(0, Math.min(sy, srcH - 1))
      sw = Math.min(sw, srcW - sx)
      sh = Math.min(sh, srcH - sy)

      if (sw <= 0 || sh <= 0) {
        processedTiles++
        continue
      }

      // 提取分片
      const tileCanvas = document.createElement('canvas')
      tileCanvas.width = sw
      tileCanvas.height = sh
      const tileCtx = tileCanvas.getContext('2d')
      tileCtx.drawImage(srcCanvas, sx, sy, sw, sh, 0, 0, sw, sh)

      const tileData = canvasToNCHW(tileCanvas)

      // 推理
      const outData = await runModel(tileData, sh, sw)

      const outSw = sw * scale
      const outSh = sh * scale
      const outSx = sx * scale
      const outSy = sy * scale

      // 计算该分片在输出中的有效区域和权重
      for (let y = 0; y < outSh; y++) {
        for (let x = 0; x < outSw; x++) {
          const oy = outSy + y
          const ox = outSx + x
          if (oy >= outH || ox >= outW) continue

          // 计算该像素在分片中的权重（边缘渐变）
          let w = 1.0
          const fadeZone = ov * scale

          // 左边缘渐变
          if (col > 0 && x < fadeZone) {
            w = Math.min(w, x / fadeZone)
          }
          // 右边缘渐变
          if (col < cols - 1 && x > outSw - fadeZone) {
            w = Math.min(w, (outSw - x) / fadeZone)
          }
          // 上边缘渐变
          if (row > 0 && y < fadeZone) {
            w = Math.min(w, y / fadeZone)
          }
          // 下边缘渐变
          if (row < rows - 1 && y > outSh - fadeZone) {
            w = Math.min(w, (outSh - y) / fadeZone)
          }

          w = Math.max(0, Math.min(1, w))

          const outIdx = oy * outW + ox
          const tilePixelIdx = y * outSw + x
          const tileTotal = outSw * outSh

          // 加权累加
          outputBuf[outIdx] += outData[tilePixelIdx] * w
          outputBuf[outIdx + outH * outW] += outData[tilePixelIdx + tileTotal] * w
          outputBuf[outIdx + 2 * outH * outW] += outData[tilePixelIdx + 2 * tileTotal] * w
          weightBuf[outIdx] += w
        }
      }

      processedTiles++
      progressPercent.value = Math.round((processedTiles / totalTiles) * 100)
      progressDetail.value = `分片 ${processedTiles} / ${totalTiles}（${cols}×${rows}）`
    }
  }

  // 除以权重得到最终结果
  const finalData = new Float32Array(3 * outH * outW)
  for (let i = 0; i < outH * outW; i++) {
    const wt = weightBuf[i] > 0 ? weightBuf[i] : 1
    finalData[i] = outputBuf[i] / wt
    finalData[i + outH * outW] = outputBuf[i + outH * outW] / wt
    finalData[i + 2 * outH * outW] = outputBuf[i + 2 * outH * outW] / wt
  }

  return nchwToCanvas(finalData, outW, outH)
}

// 强制刷新 UI - 使用 requestAnimationFrame 确保 DOM 更新
const forceUIUpdate = () => {
  return new Promise(resolve => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        resolve()
      })
    })
  })
}

// 让出主线程，使 Vue 能更新 DOM
const yieldToMain = () => new Promise(r => setTimeout(r, 10))

// 整图处理（小图直接处理）
const processFull = async (srcCanvas) => {
  const w = srcCanvas.width
  const h = srcCanvas.height

  progressDetail.value = '正在提取像素数据...'
  progressPercent.value = 10
  await forceUIUpdate()

  const inputData = canvasToNCHW(srcCanvas)

  progressDetail.value = '模型推理中，请稍候...'
  progressPercent.value = 30
  await forceUIUpdate()

  // 使用 setTimeout 让模型推理在下一个事件循环执行，避免阻塞 UI
  const outData = await new Promise((resolve, reject) => {
    setTimeout(async () => {
      try {
        const result = await runModel(inputData, h, w)
        resolve(result)
      } catch (e) {
        reject(e)
      }
    }, 50)
  })

  progressPercent.value = 80
  progressDetail.value = '正在生成结果图片...'
  await forceUIUpdate()

  const result = nchwToCanvas(outData, w * 4, h * 4)

  progressPercent.value = 95
  progressDetail.value = '即将完成...'
  await forceUIUpdate()

  return result
}

const processImage = async () => {
  if (!originalImage.value || !session) return

  isProcessing.value = true
  progressPercent.value = 0
  progressDetail.value = '准备中...'
  cancelToken = { cancelled: false }

  try {
    // 加载源图到 canvas
    const srcCanvas = document.createElement('canvas')
    const img = new Image()
    await new Promise((resolve) => {
      img.onload = resolve
      img.src = originalImage.value
    })
    srcCanvas.width = img.width
    srcCanvas.height = img.height
    srcCanvas.getContext('2d').drawImage(img, 0, 0)

    const ts = tileSize.value
    const needTile = img.width > ts || img.height > ts

    progressPercent.value = 5
    progressDetail.value = needTile ? '准备分片...' : '准备整图处理...'
    await yieldToMain()

    let resultCanvas
    if (needTile) {
      resultCanvas = await processTiled(srcCanvas)
    } else {
      resultCanvas = await processFull(srcCanvas)
    }

    if (!resultCanvas || cancelToken.cancelled) {
      ElMessage.info('处理已取消')
      return
    }

    progressPercent.value = 100
    progressDetail.value = '完成！'

    resultImage.value = resultCanvas.toDataURL('image/png')
    ElMessage.success('超分辨率处理完成')
  } catch (error) {
    if (!cancelToken.cancelled) {
      console.error('处理失败:', error)
      ElMessage.error('处理失败: ' + error.message)
    }
  } finally {
    isProcessing.value = false
  }
}

const downloadResult = () => {
  if (!resultImage.value) return
  const link = document.createElement('a')
  link.download = `super-resolution-${originalWidth.value * 4}x${originalHeight.value * 4}.png`
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

.setting-item {
  margin-bottom: 15px;
}

.setting-item:last-of-type {
  margin-bottom: 10px;
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
  min-width: 50px;
  text-align: center;
  color: var(--primary);
  font-weight: 600;
  font-size: 0.9rem;
}

.setting-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 0.8rem;
  line-height: 1.5;
  opacity: 0.7;
}

.setting-hint .el-icon {
  margin-top: 2px;
  flex-shrink: 0;
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
