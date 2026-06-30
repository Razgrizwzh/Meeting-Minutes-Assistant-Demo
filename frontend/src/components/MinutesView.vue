<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import { Download } from '@element-plus/icons-vue'
import { useMeetingStore } from '@/stores/meeting'
import GeneratingProgress from './GeneratingProgress.vue'

const meeting = useMeetingStore()

// markdown-it 实例：启用表格、删除线等
// 【安全取舍】demo 信任 LLM 输出，未做 HTML sanitize；
// 生产环境应对 v-html 内容做 DOMPurify 等过滤防 XSS。
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: false,
})

const renderedHtml = computed(() => {
  if (!meeting.currentMarkdown) return ''
  return md.render(meeting.currentMarkdown)
})
</script>

<template>
  <section class="minutes-view">
    <div class="view-header">
      <h3>会议纪要</h3>
      <el-tooltip v-if="meeting.hasMinutes && !meeting.generating" content="导出功能后续轮实现" placement="top">
        <el-button :icon="Download" disabled>导出</el-button>
      </el-tooltip>
    </div>

    <!-- 生成中：显示进度条（优先级最高） -->
    <GeneratingProgress v-if="meeting.generating" :text-length="meeting.inputLength" />

    <!-- 已有纪要：渲染 Markdown -->
    <div v-else-if="meeting.hasMinutes" class="minutes-body markdown-body" v-html="renderedHtml" />

    <!-- 空态 -->
    <el-empty
      v-else
      description="尚未生成纪要，请在上方输入会议文本后点击「生成纪要」"
      :image-size="80"
    />
  </section>
</template>

<style scoped>
.minutes-view {
  background: var(--ma-surface);
  border: 1px solid var(--ma-border);
  border-radius: var(--ma-radius);
  padding: 16px 20px;
  flex: 1 1 0;
  min-height: 240px;
  display: flex;
  flex-direction: column;
}
.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.view-header h3 {
  margin: 0;
  font-size: 16px;
}
.minutes-body {
  flex: 1;
  overflow: auto;
  line-height: 1.7;
  color: var(--ma-text);
}
</style>

<!-- Markdown 渲染样式（非 scoped，作用于 v-html 内容） -->
<style>
.markdown-body h2 {
  font-size: 20px;
  margin: 0 0 12px;
  border-bottom: 1px solid var(--ma-border);
  padding-bottom: 6px;
}
.markdown-body h3 {
  font-size: 16px;
  margin: 18px 0 8px;
  color: var(--ma-primary);
}
.markdown-body p {
  margin: 6px 0;
}
.markdown-body ul,
.markdown-body ol {
  padding-left: 22px;
  margin: 6px 0;
}
.markdown-body li {
  margin: 3px 0;
}
.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
}
.markdown-body th,
.markdown-body td {
  border: 1px solid var(--ma-border);
  padding: 6px 10px;
  text-align: left;
}
.markdown-body th {
  background: var(--ma-primary-light);
  font-weight: 600;
}
.markdown-body hr {
  border: none;
  border-top: 1px solid var(--ma-border);
  margin: 12px 0;
}
.markdown-body strong {
  font-weight: 600;
}
</style>
