<template>
  <div class="app-container">
    <!-- 动态背景 -->
    <div class="bg-animation">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
      <div class="grid-overlay"></div>
    </div>

    <!-- 头部 -->
    <header class="header">
      <div class="header-content">
        <div class="logo">
          <div class="logo-icon">
            <div class="logo-glow"></div>
            <el-icon size="36" color="#00f0ff"><MagicStick /></el-icon>
          </div>
          <div class="logo-text">
            <h1>AI IMAGE<span class="highlight">LAB</span></h1>
            <div class="logo-subtitle">智能图像处理实验室</div>
          </div>
        </div>
        <p class="subtitle">
          <span class="tech-badge">
            <el-icon><Cpu /></el-icon>
            WebAssembly 本地运行
          </span>
          <span class="tech-badge">
            <el-icon><Lock /></el-icon>
            隐私保护
          </span>
        </p>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 功能选择卡片 -->
      <div class="feature-selector">
        <div 
          class="feature-card" 
          :class="{ active: activeFeature === 'matting' }"
          @click="switchFeature('matting')"
        >
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="feature-icon">
              <el-icon size="32"><Crop /></el-icon>
            </div>
            <h3>智能抠图</h3>
            <p>AI 人像分割，透明背景输出</p>
            <div class="feature-tags">
              <span class="tag">RVM ResNet50</span>
              <span class="tag">FP16</span>
            </div>
          </div>
        </div>

        <div 
          class="feature-card" 
          :class="{ active: activeFeature === 'superresolution' }"
          @click="switchFeature('superresolution')"
        >
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="feature-icon">
              <el-icon size="32"><ZoomIn /></el-icon>
            </div>
            <h3>超分辨率</h3>
            <p>4倍放大，细节增强</p>
            <div class="feature-tags">
              <span class="tag">Real-ESRGAN</span>
              <span class="tag">4x</span>
            </div>
          </div>
        </div>

        <div 
          class="feature-card" 
          :class="{ active: activeFeature === 'colorization' }"
          @click="switchFeature('colorization')"
        >
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="feature-icon">
              <el-icon size="32"><Brush /></el-icon>
            </div>
            <h3>黑白上色</h3>
            <p>老照片智能上色</p>
            <div class="feature-tags">
              <span class="tag">DDColor</span>
              <span class="tag">INT8</span>
            </div>
          </div>
        </div>

        <div 
          class="feature-card" 
          :class="{ active: activeFeature === 'codeformer' }"
          @click="switchFeature('codeformer')"
        >
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="feature-icon">
              <el-icon size="32"><FirstAidKit /></el-icon>
            </div>
            <h3>老照片修复</h3>
            <p>人脸修复，去除模糊划痕</p>
            <div class="feature-tags">
              <span class="tag">CodeFormer</span>
              <span class="tag">FP16</span>
            </div>
          </div>
        </div>

        <div 
          class="feature-card" 
          :class="{ active: activeFeature === 'chat' }"
          @click="switchFeature('chat')"
        >
          <div class="card-glow"></div>
          <div class="card-content">
            <div class="feature-icon">
              <el-icon size="32"><ChatDotRound /></el-icon>
            </div>
            <h3>AI对话</h3>
            <p>浏览器本地运行大模型</p>
            <div class="feature-tags">
              <span class="tag">Qwen2.5-0.5B</span>
              <span class="tag">INT4</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 功能面板 -->
      <div class="panel-wrapper">
        <MattingPanel 
          v-if="activeFeature === 'matting'" 
          ref="mattingPanelRef"
        />
        <SuperResolutionPanel 
          v-else-if="activeFeature === 'superresolution'" 
          ref="srPanelRef"
        />
        <ColorizationPanel 
          v-else-if="activeFeature === 'colorization'" 
          ref="colorizationPanelRef"
        />
        <CodeFormerPanel 
          v-else-if="activeFeature === 'codeformer'" 
          ref="codeformerPanelRef"
        />
        <ChatPanel 
          v-else 
          ref="chatPanelRef"
        />
      </div>
    </main>

    <!-- 底部 -->
    <footer class="footer">
      <div class="footer-content">
        <div class="footer-line"></div>
        <p>AI IMAGE LAB</p>
        <p class="footer-sub">Powered by ONNX Runtime Web</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Cpu, Lock, Crop, ZoomIn, Brush, FirstAidKit, ChatDotRound } from '@element-plus/icons-vue'
import MattingPanel from './components/MattingPanel.vue'
import SuperResolutionPanel from './components/SuperResolutionPanel.vue'
import ColorizationPanel from './components/ColorizationPanel.vue'
import CodeFormerPanel from './components/CodeFormerPanel.vue'
import ChatPanel from './components/ChatPanel.vue'

const activeFeature = ref('matting')
const mattingPanelRef = ref(null)
const srPanelRef = ref(null)
const colorizationPanelRef = ref(null)
const codeformerPanelRef = ref(null)
const chatPanelRef = ref(null)

// 切换功能：v-if会自动销毁旧组件(onUnmounted释放模型)并创建新组件(onMounted加载模型)
const switchFeature = (feature) => {
  if (activeFeature.value === feature) return
  activeFeature.value = feature
}

const getFeatureName = (feature) => {
  const names = {
    'matting': '智能抠图',
    'superresolution': '超分辨率',
    'colorization': '黑白上色'
  }
  return names[feature] || feature
}

onMounted(() => {
  console.log('AI Image Lab 已启动')
  console.log('支持功能: 智能抠图、超分辨率、黑白上色')
})
</script>

<style>
/* 全局样式 */
:root {
  --primary: #00f0ff;
  --secondary: #7000ff;
  --accent: #ff00a0;
  --bg-dark: #0a0a0f;
  --bg-card: rgba(20, 20, 30, 0.8);
  --bg-card-hover: rgba(30, 30, 45, 0.9);
  --text-primary: #ffffff;
  --text-secondary: #a0a0b0;
  --border-glow: rgba(0, 240, 255, 0.3);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg-dark);
  color: var(--text-primary);
  overflow-x: hidden;
}
</style>

<style scoped>
.app-container {
  min-height: 100vh;
  position: relative;
  background: var(--bg-dark);
}

/* 动态背景 */
.bg-animation {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: float 20s ease-in-out infinite;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, var(--secondary) 0%, transparent 70%);
  top: -200px;
  right: -100px;
  animation-delay: 0s;
}

.orb-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
  bottom: -150px;
  left: -100px;
  animation-delay: -7s;
}

.orb-3 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, var(--accent) 0%, transparent 70%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.1); }
  66% { transform: translate(-20px, 20px) scale(0.9); }
}

.grid-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
}

/* 头部 */
.header {
  position: relative;
  z-index: 10;
  padding: 40px 20px;
  text-align: center;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 20px;
}

.logo-icon {
  position: relative;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.1), rgba(112, 0, 255, 0.1));
  border: 1px solid var(--border-glow);
  border-radius: 16px;
}

.logo-glow {
  position: absolute;
  inset: -2px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 16px;
  opacity: 0.5;
  filter: blur(10px);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.logo-text h1 {
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #fff 0%, var(--primary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-text .highlight {
  color: var(--primary);
  -webkit-text-fill-color: var(--primary);
}

.logo-subtitle {
  font-size: 0.9rem;
  color: var(--text-secondary);
  letter-spacing: 4px;
  text-transform: uppercase;
}

.subtitle {
  display: flex;
  justify-content: center;
  gap: 15px;
  flex-wrap: wrap;
}

.tech-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.2);
  border-radius: 20px;
  font-size: 0.85rem;
  color: var(--primary);
}

/* 主内容 */
.main-content {
  position: relative;
  z-index: 10;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

/* 功能选择器 */
.feature-selector {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.feature-card {
  position: relative;
  background: var(--bg-card);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 30px;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
}

.feature-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-glow);
  transform: translateY(-5px);
}

.feature-card.active {
  background: linear-gradient(135deg, rgba(0, 240, 255, 0.1), rgba(112, 0, 255, 0.1));
  border-color: var(--primary);
  box-shadow: 0 0 30px rgba(0, 240, 255, 0.2);
}

.card-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 0%, rgba(0, 240, 255, 0.15), transparent 70%);
  opacity: 0;
  transition: opacity 0.3s;
}

.feature-card:hover .card-glow,
.feature-card.active .card-glow {
  opacity: 1;
}

.card-content {
  position: relative;
  z-index: 1;
}

.feature-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 16px;
  margin-bottom: 20px;
  color: white;
}

.feature-card h3 {
  font-size: 1.4rem;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.feature-card p {
  color: var(--text-secondary);
  font-size: 0.95rem;
  margin-bottom: 15px;
}

.feature-tags {
  display: flex;
  gap: 8px;
}

.tag {
  padding: 4px 10px;
  background: rgba(0, 240, 255, 0.1);
  border: 1px solid rgba(0, 240, 255, 0.2);
  border-radius: 12px;
  font-size: 0.75rem;
  color: var(--primary);
}

/* 面板包装 */
.panel-wrapper {
  background: var(--bg-card);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 30px;
  backdrop-filter: blur(10px);
}

/* 底部 */
.footer {
  position: relative;
  z-index: 10;
  padding: 40px 20px;
  text-align: center;
}

.footer-content {
  max-width: 600px;
  margin: 0 auto;
}

.footer-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary), transparent);
  margin-bottom: 20px;
}

.footer p {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.footer-sub {
  margin-top: 5px;
  font-size: 0.8rem;
  opacity: 0.6;
}

@media (max-width: 768px) {
  .logo-text h1 {
    font-size: 1.8rem;
  }
  
  .feature-selector {
    grid-template-columns: 1fr;
  }
  
  .panel-wrapper {
    padding: 20px;
  }
}
</style>
