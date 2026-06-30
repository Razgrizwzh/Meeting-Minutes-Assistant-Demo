<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload, Document } from '@element-plus/icons-vue'
import { useMeetingStore } from '@/stores/meeting'

const meeting = useMeetingStore()

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
  <section class="meeting-input">
    <div class="input-header">
      <h3>会议输入</h3>
      <div class="meta-row">
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
    </div>

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
  </section>
</template>

<style scoped>
.meeting-input {
  background: var(--ma-surface);
  border: 1px solid var(--ma-border);
  border-radius: var(--ma-radius);
  padding: 16px 20px;
}
.input-header h3 {
  margin: 0 0 12px;
  font-size: 16px;
}
.meta-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.meta-name {
  flex: 1;
}
.meta-date {
  width: 160px;
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
