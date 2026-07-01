<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Document, ArrowUp, ArrowDown } from '@element-plus/icons-vue'
import { useMeetingStore } from '@/stores/meeting'
import { useUiStore } from '@/stores/ui'

const meeting = useMeetingStore()
const ui = useUiStore()

const activeTab = ref('paste')
const form = reactive({
  text: '',
  meetingName: '',
  date: new Date().toISOString().slice(0, 10),
})
const selectedFile = ref(null)
const fileInput = ref(null)

function handleFileChange(uploadFile) {
  selectedFile.value = uploadFile.raw
}

function handleFileRemove() {
  selectedFile.value = null
}

async function handleGenerate() {
  // 校验输入
  if (activeTab.value === 'paste') {
    if (!form.text.trim()) {
      ElMessage.warning('请输入会议转写文本')
      return
    }
  } else {
    if (!selectedFile.value) {
      ElMessage.warning('请上传会议文件（.txt 或 .docx）')
      return
    }
  }

  const payload = {
    meetingName: form.meetingName || undefined,
    date: form.date || undefined,
  }
  if (activeTab.value === 'paste') {
    payload.text = form.text
  } else {
    payload.file = selectedFile.value
  }

  try {
    // 生成期间在纪要区显示进度条，这里无需额外提示
    await meeting.generate(payload)
    ElMessage.success('纪要生成成功')
    // 生成成功后自动切到「会议纪要」Tab 展示结果
    ui.setActiveMainTab('minutes')
  } catch (err) {
    // 区分超时/网络错误与后端业务错误
    let detail
    if (err.code === 'ECONNABORTED' || /timeout/i.test(err.message || '')) {
      detail = '生成超时，请稍后重试或缩短文本'
    } else if (err.response?.data?.detail) {
      detail = err.response.data.detail
    } else {
      detail = '生成失败，请重试'
    }
    ElMessage.error(detail)
  }
}
</script>

<template>
  <section class="meeting-input" :class="{ collapsed: ui.inputCollapsed }">
    <div class="input-header">
      <h3>会议输入</h3>
      <div class="meta-row" v-show="!ui.inputCollapsed">
        <el-input
          v-model="form.meetingName"
          placeholder="会议名称（可选）"
          class="meta-name"
          clearable
        />
        <el-date-picker
          v-model="form.date"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="会议日期"
          class="meta-date"
        />
      </div>
      <el-button
        class="collapse-btn"
        link
        :icon="ui.inputCollapsed ? ArrowDown : ArrowUp"
        :title="ui.inputCollapsed ? '展开输入区' : '收起输入区'"
        @click="ui.toggleInputCollapsed"
      />
    </div>

    <template v-if="!ui.inputCollapsed">
      <el-tabs v-model="activeTab" class="input-tabs">
        <el-tab-pane label="文本粘贴" name="paste">
          <el-input
            v-model="form.text"
            type="textarea"
            :rows="6"
            placeholder="粘贴会议转写文本…"
            maxlength="20000"
            show-word-limit
          />
        </el-tab-pane>

        <el-tab-pane label="文件上传" name="upload">
          <el-upload
            ref="fileInput"
            drag
            :auto-upload="false"
            :limit="1"
            accept=".txt,.log,.docx"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-icon class="upload-icon"><Upload /></el-icon>
            <div class="upload-text">拖拽文件到此处，或点击上传</div>
            <template #tip>
              <div class="upload-tip">支持 .txt（自动检测编码）、.docx 格式</div>
            </template>
          </el-upload>
        </el-tab-pane>
      </el-tabs>

      <div class="input-footer">
        <el-button
          type="primary"
          :loading="meeting.generating"
          :icon="Document"
          @click="handleGenerate"
        >
          生成纪要
        </el-button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.meeting-input {
  background: var(--ma-surface);
  border: 1px solid var(--ma-border);
  border-radius: var(--ma-radius);
  padding: 16px 20px;
  /* 收起时收缩为一行标题栏 */
  transition: padding 0.2s ease;
}
.meeting-input.collapsed {
  padding-bottom: 12px;
}
.input-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.input-header h3 {
  margin: 0;
  font-size: 16px;
}
.meta-row {
  display: flex;
  gap: 12px;
  flex: 1;
  min-width: 200px;
}
.meta-name {
  flex: 1;
}
.meta-date {
  width: 160px;
}
.collapse-btn {
  margin-left: auto;
}
.input-tabs {
  margin-top: 12px;
}
.input-tabs :deep(.el-textarea__inner) {
  resize: vertical;
}
.upload-icon {
  font-size: 32px;
  color: var(--ma-text-secondary);
}
.upload-text {
  font-size: 13px;
  color: var(--ma-text-secondary);
  margin-top: 6px;
}
.upload-tip {
  font-size: 12px;
  color: var(--ma-text-secondary);
  margin-top: 4px;
}
.input-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
