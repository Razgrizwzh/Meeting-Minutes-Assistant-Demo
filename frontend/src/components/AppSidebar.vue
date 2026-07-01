<script setup>
import { watch, ref } from 'vue'
import { Fold, Expand, Clock, Document, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useMeetingStore } from '@/stores/meeting'

const auth = useAuthStore()
const ui = useUiStore()
const meeting = useMeetingStore()

// 当前选中的历史项 id（高亮）
const activeId = ref(null)
// 正在删除的项 id（按钮 loading）
const deletingId = ref(null)

// 登录状态变化时加载/清空历史
watch(
  () => auth.isLoggedIn,
  (logged) => {
    if (logged) {
      meeting.loadHistory().catch(() => ElMessage.error('加载历史失败'))
    } else {
      meeting.history = []
    }
  },
  { immediate: true },
)

async function openMeeting(item) {
  if (activeId.value === item.meeting_id) return
  activeId.value = item.meeting_id
  try {
    await meeting.loadMeeting(item.meeting_id)
  } catch (err) {
    const detail = err.response?.data?.detail || '加载会议详情失败'
    ElMessage.error(detail)
    activeId.value = null
  }
}

async function onDeleteClick(item) {
  // ElMessageBox.confirm 返回 promise，用户点取消时 reject('cancel')，需吞掉以免报错
  try {
    await ElMessageBox.confirm(
      `确定删除「${item.meeting_name}」吗？该会议纪要将被永久删除。`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return // 用户取消
  }

  deletingId.value = item.meeting_id
  try {
    const { wasCurrent } = await meeting.removeMeeting(item.meeting_id)
    if (activeId.value === item.meeting_id) activeId.value = null
    ElMessage.success(wasCurrent ? '已删除，当前查看的纪要已清空' : '已删除')
  } catch (err) {
    const raw = err.response?.data?.detail
    const detail = Array.isArray(raw) ? raw[0]?.msg : raw || '删除失败，请重试'
    ElMessage.error(detail)
  } finally {
    deletingId.value = null
  }
}
</script>

<template>
  <aside class="app-sidebar" :class="{ collapsed: ui.sidebarCollapsed }">
    <div class="sidebar-head">
      <el-icon class="title-icon"><Clock /></el-icon>
      <span v-show="!ui.sidebarCollapsed" class="title-text">历史会议</span>
      <el-button
        class="collapse-btn"
        link
        @click="ui.toggleSidebar"
        :title="ui.sidebarCollapsed ? '展开' : '折叠'"
      >
        <el-icon><Fold v-if="!ui.sidebarCollapsed" /><Expand v-else /></el-icon>
      </el-button>
    </div>

    <div class="sidebar-body">
      <el-empty
        v-if="!auth.isLoggedIn"
        description="登录后显示历史会议"
        :image-size="60"
      />
      <el-empty
        v-else-if="meeting.history.length === 0"
        description="暂无历史会议"
        :image-size="60"
      />
      <ul v-else class="history-list">
        <li
          v-for="item in meeting.history"
          :key="item.meeting_id"
          class="history-item"
          :class="{ active: activeId === item.meeting_id }"
          @click="openMeeting(item)"
          :title="item.meeting_name"
        >
          <el-icon class="item-icon"><Document /></el-icon>
          <div class="item-info">
            <div class="item-name">{{ item.meeting_name }}</div>
            <div class="item-date">{{ item.date || '—' }}</div>
          </div>
          <el-button
            v-show="!ui.sidebarCollapsed"
            class="item-delete"
            link
            :icon="Delete"
            :loading="deletingId === item.meeting_id"
            @click.stop="onDeleteClick(item)"
            title="删除"
          />
        </li>
      </ul>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  width: var(--ma-sidebar-w);
  background: var(--ma-surface);
  border-right: 1px solid var(--ma-border);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease, background-color 0.25s ease, border-color 0.25s ease;
  box-shadow: 1px 0 0 var(--ma-border-light);
}
.app-sidebar.collapsed {
  width: var(--ma-sidebar-w-collapsed);
}
.sidebar-head {
  height: 48px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border-bottom: 1px solid var(--ma-border-light);
}
.title-icon {
  color: var(--ma-primary);
  font-size: 16px;
}
.title-text {
  font-size: 14px;
  font-weight: 600;
  flex: 1;
}
.collapse-btn {
  margin-left: auto;
}
.sidebar-body {
  flex: 1;
  overflow: auto;
  padding: 12px 8px;
}
.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--ma-radius-sm);
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.15s ease, color 0.15s ease;
}
.history-item:hover {
  background: var(--ma-primary-light);
}
.history-item.active {
  background: var(--ma-primary);
  color: #fff;
}
.history-item.active .item-date {
  color: rgba(255, 255, 255, 0.8);
}
.item-delete {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s;
  color: var(--ma-text-secondary);
}
.history-item:hover .item-delete {
  opacity: 1;
}
.item-delete:hover {
  color: var(--ma-danger, #f56c6c);
}
.history-item.active .item-delete {
  color: rgba(255, 255, 255, 0.85);
}
.history-item.active .item-delete:hover {
  color: #fff;
}
.item-icon {
  font-size: 16px;
  flex-shrink: 0;
}
.item-info {
  flex: 1;
  min-width: 0;
}
.item-name {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-date {
  font-size: 11px;
  color: var(--ma-text-secondary);
}
</style>
