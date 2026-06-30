<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'

const props = defineProps({
  // 输入文本长度，用于预估生成时长分档
  textLength: { type: Number, default: 0 },
})

// 按文本长度预估总时长（秒）。qwen-plus 实测：中等长度约 20-40s，长文本更长。
// 这里给偏宽松的预估，避免过早显示"超时"。
const estimate = computed(() => {
  const n = props.textLength || 0
  if (n < 300) return 30
  if (n < 1000) return 60
  if (n < 2000) return 90
  return 120
})

// 状态文案轮换
const statusMessages = [
  '正在阅读会议转写文本…',
  '正在提炼核心议题与讨论要点…',
  '正在归纳决策结论…',
  '正在整理待办事项与负责人…',
  '正在生成结构化纪要…',
  '即将完成，请稍候…',
]

const elapsed = ref(0)
const statusIdx = ref(0)
let timer = null
let statusTimer = null

function start() {
  stop()
  elapsed.value = 0
  statusIdx.value = 0
  timer = setInterval(() => {
    elapsed.value += 1
  }, 1000)
  // 每 8 秒轮换状态文案
  statusTimer = setInterval(() => {
    statusIdx.value = Math.min(statusIdx.value + 1, statusMessages.length - 1)
  }, 8000)
}

function stop() {
  if (timer) clearInterval(timer), (timer = null)
  if (statusTimer) clearInterval(statusTimer), (statusTimer = null)
}

// 启动计时；组件卸载时清理
start()
onUnmounted(stop)

// 进度（0-100）：未到预估时间按缓动曲线逼近 95%；超过预估后停在 92%
const progress = computed(() => {
  const e = elapsed.value
  const est = estimate.value
  if (e < est) {
    // 缓动：前半段推进快，后半段放缓，最多到 95%
    const ratio = e / est
    return Math.round((1 - Math.pow(1 - ratio, 2)) * 95)
  }
  // 超过预估：停在 92%，留主进度条一点悬念直到真正完成
  return 92
})

const overEstimate = computed(() => elapsed.value > estimate.value)
const formattedElapsed = computed(() => {
  const m = Math.floor(elapsed.value / 60)
  const s = elapsed.value % 60
  return m > 0 ? `${m}分${s.toString().padStart(2, '0')}秒` : `${s}秒`
})
</script>

<template>
  <div class="generating-progress">
    <div class="gp-header">
      <el-icon class="gp-icon is-loading"><Loading /></el-icon>
      <span class="gp-title">正在生成会议纪要</span>
      <span class="gp-elapsed">{{ formattedElapsed }}</span>
    </div>

    <el-progress
      :percentage="progress"
      :stroke-width="10"
      :show-text="false"
      status="success"
      class="gp-bar"
    />

    <div class="gp-status-row">
      <span class="gp-status">{{ statusMessages[statusIdx] }}</span>
      <span class="gp-estimate">
        预估 {{ estimate }} 秒左右{{ overEstimate ? '（比预估稍久，仍在生成…）' : '' }}
      </span>
    </div>

    <div class="gp-hint">生成完成后会自动展示纪要，请勿离开页面</div>
  </div>
</template>

<style scoped>
.generating-progress {
  padding: 8px 4px;
}
.gp-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}
.gp-icon {
  font-size: 18px;
  color: var(--ma-primary);
}
.is-loading {
  animation: gp-rotate 1.2s linear infinite;
}
@keyframes gp-rotate {
  to { transform: rotate(360deg); }
}
.gp-title {
  font-size: 15px;
  font-weight: 600;
}
.gp-elapsed {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
  font-size: 14px;
  color: var(--ma-text-secondary);
}
.gp-bar {
  margin-bottom: 10px;
}
.gp-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.gp-status {
  font-size: 13px;
  color: var(--ma-text);
}
.gp-estimate {
  font-size: 12px;
  color: var(--ma-text-secondary);
}
.gp-hint {
  font-size: 12px;
  color: var(--ma-text-secondary);
}
</style>