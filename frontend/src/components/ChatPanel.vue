<template>
  <div class="panel-container chat-panel">
    <!-- 模型加载状态 -->
    <div v-if="modelStatus !== 'ready'" class="status-bar" :class="modelStatus">
      <div class="status-indicator"></div>
      <span>{{ modelStatusText }}</span>
      <button v-if="modelStatus === 'error'" class="retry-btn" @click="loadModel">重试</button>
    </div>

    <!-- 聊天区域 -->
    <div class="chat-container" ref="chatContainer">
      <div class="messages">
        <div v-for="(msg, idx) in messages" :key="idx" 
             class="message" :class="msg.role">
          <div class="message-avatar">
            <span v-if="msg.role === 'user'">👤</span>
            <span v-else>🤖</span>
          </div>
          <div class="message-content">
            <div class="message-header">
              <span class="role">{{ msg.role === 'user' ? '你' : 'AI助手' }}</span>
              <span class="time">{{ msg.time }}</span>
            </div>
            <div class="message-text">{{ msg.content }}</div>
          </div>
        </div>
        
        <!-- 正在生成中 -->
        <div v-if="isGenerating" class="message assistant generating">
          <div class="message-avatar">🤖</div>
          <div class="message-content">
            <div class="message-header">
              <span class="role">AI助手</span>
              <span class="generating-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </span>
            </div>
            <div class="message-text">{{ currentResponse }}<span class="cursor">▌</span></div>
          </div>
        </div>
      </div>
      
      <div v-if="messages.length === 0 && modelStatus === 'ready'" class="empty-chat">
        <div class="empty-icon">💬</div>
        <p>开始与 AI 对话吧！</p>
        <p class="hint">模型将首次下载到浏览器缓存（约600MB）</p>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-section">
      <div class="input-wrapper">
        <textarea 
          v-model="userInput"
          class="chat-input"
          placeholder="输入消息开始对话..."
          :disabled="isGenerating || modelStatus !== 'ready'"
          @keydown.enter.exact.prevent="sendMessage"
          rows="2"
        ></textarea>
        <button 
          class="send-btn"
          :disabled="!userInput.trim() || isGenerating || modelStatus !== 'ready'"
          @click="sendMessage"
        >
          发送
        </button>
      </div>
      <div class="input-hints">
        <span class="hint">Enter 发送</span>
        <span class="model-info" v-if="modelStatus === 'ready'">
          ✓ Qwen2.5-0.5B INT4 已加载
        </span>
      </div>
    </div>

    <!-- 设置面板 -->
    <div class="settings-section">
      <div class="setting-card">
        <div class="setting-header">⚙️ 生成参数</div>
        <div class="setting-body">
          <div class="param-row">
            <span class="param-label">Temperature</span>
            <span class="param-value">{{ temperature.toFixed(1) }}</span>
          </div>
          <input type="range" min="0.1" max="2.0" step="0.1" v-model.number="temperature" class="slider" />
          
          <div class="param-row" style="margin-top: 15px;">
            <span class="param-label">Max Tokens</span>
            <span class="param-value">{{ maxTokens }}</span>
          </div>
          <input type="range" min="64" max="2048" step="64" v-model.number="maxTokens" class="slider" />
        </div>
      </div>

      <button class="clear-btn" @click="clearHistory" :disabled="messages.length === 0">
        🗑️ 清空对话
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage } from 'element-plus'

const modelStatus = ref('loading')
const messages = ref([])
const userInput = ref('')
const isGenerating = ref(false)
const currentResponse = ref('')
const chatContainer = ref(null)

const temperature = ref(0.7)
const maxTokens = ref(512)

let generator = null
let tokenizer = null

const modelStatusText = computed(() => {
  switch (modelStatus.value) {
    case 'loading': return '正在加载模型...'
    case 'error': return '模型加载失败'
    case 'ready': return ''
    default: return ''
  }
})

// 加载模型
const loadModel = async () => {
  modelStatus.value = 'loading'
  try {
    const { pipeline, env } = await import('@huggingface/transformers')
    
    // 使用国内镜像站 HF-Mirror
    env.remoteHost = 'https://hf-mirror.com'
    env.allowLocalModels = false
    
    // 加载 text-generation pipeline
    generator = await pipeline(
      'text-generation',
      'onnx-community/Qwen2.5-0.5B-Instruct',
      {
        dtype: 'q4',
        device: 'auto',
      }
    )
    
    // 获取 tokenizer 用于应用 chat template
    tokenizer = generator.tokenizer
    
    modelStatus.value = 'ready'
    ElMessage.success('模型加载成功！')
  } catch (error) {
    console.error('模型加载失败:', error)
    modelStatus.value = 'error'
    ElMessage.error('模型加载失败: ' + error.message)
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// 构建聊天提示词（使用 Qwen 的 chat template）
const buildPrompt = () => {
  // Qwen2.5 chat template
  // <|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant\n
  let prompt = '<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n'
  
  for (const msg of messages.value) {
    if (msg.role === 'user') {
      prompt += `<|im_start|>user\n${msg.content}<|im_end|>\n`
    } else {
      prompt += `<|im_start|>assistant\n${msg.content}<|im_end|>\n`
    }
  }
  
  prompt += '<|im_start|>assistant\n'
  return prompt
}

// 发送消息
const sendMessage = async () => {
  const text = userInput.value.trim()
  if (!text || isGenerating.value || modelStatus.value !== 'ready') return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: text,
    time: new Date().toLocaleTimeString()
  })
  userInput.value = ''
  await scrollToBottom()

  // 开始生成
  isGenerating.value = true
  currentResponse.value = ''

  try {
    // 构建带 chat template 的提示词
    const prompt = buildPrompt()
    
    // 流式生成
    let fullResponse = ''
    
    // 使用 generator 进行流式生成
    const result = await generator(prompt, {
      max_new_tokens: maxTokens.value,
      temperature: temperature.value,
      do_sample: true,
      top_p: 0.9,
      return_full_text: false,  // 只返回新生成的内容
    })
    
    // 提取生成的文本
    let generatedText = result[0].generated_text
    
    // 清理：移除可能的结束标记和后续内容
    const endMarkers = ['<|im_end|>', '<|im_start|>', '\n\n\n']
    for (const marker of endMarkers) {
      const idx = generatedText.indexOf(marker)
      if (idx !== -1) {
        generatedText = generatedText.substring(0, idx)
      }
    }
    
    // 模拟流式输出效果
    const chars = generatedText.split('')
    for (let i = 0; i < chars.length; i++) {
      fullResponse += chars[i]
      currentResponse.value = fullResponse
      await scrollToBottom()
      // 小延迟模拟打字效果
      await new Promise(r => setTimeout(r, 20))
    }
    
    // 添加助手回复
    messages.value.push({
      role: 'assistant',
      content: fullResponse,
      time: new Date().toLocaleTimeString()
    })

  } catch (error) {
    console.error('生成失败:', error)
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    isGenerating.value = false
    currentResponse.value = ''
    await scrollToBottom()
  }
}

// 清空历史
const clearHistory = () => {
  messages.value = []
}

onMounted(() => {
  loadModel()
})

onUnmounted(() => {
  // 释放模型资源
  if (generator) {
    generator.dispose?.()
    generator = null
  }
  if (tokenizer) {
    tokenizer = null
  }
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
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

.retry-btn {
  margin-left: auto;
  padding: 6px 16px;
  background: var(--primary);
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  font-size: 0.85rem;
}

/* 聊天容器 */
.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 16px;
  margin-bottom: 20px;
  max-height: 400px;
  min-height: 200px;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 1.2rem;
  background: rgba(255, 255, 255, 0.1);
}

.message-content {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 12px 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.message.user .message-content {
  background: rgba(0, 240, 255, 0.1);
  border-color: rgba(0, 240, 255, 0.2);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.role {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.9rem;
}

.time {
  font-size: 0.7rem;
  color: var(--text-secondary);
}

.message-text {
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
  font-size: 0.95rem;
}

/* 光标动画 */
.cursor {
  animation: cursorBlink 1s step-end infinite;
  color: var(--primary);
}

@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* 空状态 */
.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 10px;
}

.empty-chat .hint {
  font-size: 0.8rem;
  opacity: 0.7;
}

/* 生成中动画 */
.generating-indicator {
  display: flex;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  background: var(--primary);
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 输入区域 */
.input-section {
  margin-bottom: 20px;
}

.input-wrapper {
  display: flex;
  gap: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 10px;
}

.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 0.95rem;
  resize: none;
  outline: none;
  font-family: inherit;
  line-height: 1.5;
}

.chat-input::placeholder {
  color: var(--text-secondary);
}

.send-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, var(--primary), var(--secondary));
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.02);
  box-shadow: 0 5px 20px rgba(0, 240, 255, 0.3);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-hints {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  padding: 0 5px;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.model-info {
  color: var(--primary);
}

/* 设置区域 */
.settings-section {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.setting-card {
  flex: 1;
  min-width: 200px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 15px;
}

.setting-header {
  margin-bottom: 12px;
  color: var(--primary);
  font-weight: 500;
}

.param-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.param-label {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.param-value {
  color: var(--primary);
  font-weight: 600;
}

.slider {
  width: 100%;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
}

.clear-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(255, 0, 100, 0.1);
  border: 1px solid rgba(255, 0, 100, 0.3);
  border-radius: 10px;
  color: #ff0064;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s;
}

.clear-btn:hover:not(:disabled) {
  background: rgba(255, 0, 100, 0.2);
}

.clear-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
