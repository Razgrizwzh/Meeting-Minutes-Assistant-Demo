<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const ui = useUiStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
})

const isRegister = computed(() => ui.authMode === 'register')

// 切换模式 / 关闭时重置表单
watch(
  () => ui.authDialogVisible,
  (visible) => {
    if (visible) {
      form.username = ''
      form.password = ''
      form.confirmPassword = ''
      formRef.value?.clearValidate()
    }
  },
)

const validateConfirm = (rule, value, callback) => {
  if (isRegister.value && value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = computed(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    {
      pattern: /^[A-Za-z0-9_]{3,32}$/,
      message: '3-32 位，仅字母、数字、下划线',
      trigger: 'blur',
    },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirmPassword: isRegister.value
    ? [{ required: true, message: '请再次输入密码', trigger: 'blur' }, { validator: validateConfirm, trigger: 'blur' }]
    : [],
}))

async function submit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      if (isRegister.value) {
        await auth.register(form.username, form.password)
        ElMessage.success('注册成功')
      } else {
        await auth.login(form.username, form.password)
        ElMessage.success('登录成功')
      }
      ui.closeAuth()
    } catch (err) {
      const detail = err.response?.data?.detail || '操作失败，请重试'
      ElMessage.error(detail)
    } finally {
      loading.value = false
    }
  })
}

function switchMode(mode) {
  ui.openAuth(mode)
}
</script>

<template>
  <el-dialog
    v-model="ui.authDialogVisible"
    :title="isRegister ? '注册' : '登录'"
    width="380px"
    :close-on-click-modal="false"
    align-center
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="3-32 位字母/数字/下划线" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
      </el-form-item>
      <el-form-item v-if="isRegister" label="确认密码" prop="confirmPassword">
        <el-input v-model="form.confirmPassword" type="password" show-password placeholder="再次输入密码" />
      </el-form-item>
    </el-form>

    <div class="mode-switch">
      <span v-if="isRegister">
        已有账号？<el-link type="primary" :underline="false" @click="switchMode('login')">去登录</el-link>
      </span>
      <span v-else>
        还没账号？<el-link type="primary" :underline="false" @click="switchMode('register')">去注册</el-link>
      </span>
    </div>

    <template #footer>
      <el-button @click="ui.closeAuth()">取消</el-button>
      <el-button type="primary" :loading="loading" @click="submit">
        {{ isRegister ? '注册' : '登录' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.mode-switch {
  text-align: center;
  font-size: 13px;
  color: var(--ma-text-secondary);
  margin-top: -8px;
}
</style>
