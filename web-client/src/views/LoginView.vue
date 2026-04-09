<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { createUserAPI, loginAPI } from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'
import { useUserStore } from '@/stores/userStore'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const isSubmitting = ref(false)
const mode = ref<'login' | 'register'>('login')
const registerUsername = ref('')
const registerPhone = ref('')
const registerEmail = ref('')
const registerPassword = ref('')
const registerConfirmPassword = ref('')

const resolvePermissions = (name: string): string[] => {
  if (name.toLowerCase() === 'admin') return ['user:manage']
  return []
}

const submitLogin = async () => {
  if (!username.value.trim() || !password.value.trim()) {
    message.warning('请输入用户名和密码')
    return
  }
  if (isSubmitting.value) return

  isSubmitting.value = true
  try {
    const result = await loginAPI({
      username: username.value.trim(),
      password: password.value
    })
    const permissions = resolvePermissions(result.user.username || '')
    authStore.setSession({
      accessToken: result.access_token,
      refreshToken: result.refresh_token,
      user: result.user,
      permissions
    })
    userStore.setUid(String(result.user.uid || '').trim())
    message.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect || '/')
  } catch (error: any) {
    message.error(error?.response?.data?.detail || error?.message || '登录失败')
  } finally {
    isSubmitting.value = false
  }
}

const submitRegister = async () => {
  if (
    !registerUsername.value.trim() ||
    !registerPhone.value.trim() ||
    !registerPassword.value.trim() ||
    !registerConfirmPassword.value.trim()
  ) {
    message.warning('请完整填写注册信息')
    return
  }
  if (registerPassword.value !== registerConfirmPassword.value) {
    message.warning('两次输入的密码不一致')
    return
  }
  if (isSubmitting.value) return

  isSubmitting.value = true
  try {
    await createUserAPI({
      username: registerUsername.value.trim(),
      phone: registerPhone.value.trim(),
      password: registerPassword.value,
      email: registerEmail.value.trim() || undefined
    })
    message.success('注册成功，请登录')
    username.value = registerUsername.value.trim()
    password.value = registerPassword.value
    registerUsername.value = ''
    registerPhone.value = ''
    registerEmail.value = ''
    registerPassword.value = ''
    registerConfirmPassword.value = ''
    mode.value = 'login'
  } catch (error: any) {
    message.error(error?.response?.data?.detail || error?.message || '注册失败')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-bgMain flex items-center justify-center px-4">
    <div class="w-full max-w-md bg-card border border-border rounded-lg shadow-sm p-6">
      <div class="mb-6">
        <h1 class="text-xl font-semibold text-textMain">登录</h1>
        <p class="text-xs text-textMute mt-1">请输入账号密码访问交易平台</p>
      </div>

      <div class="flex items-center rounded border border-border p-0.5 bg-bgMain/70 text-xs mb-4">
        <button
          type="button"
          class="flex-1 px-4 py-1 rounded font-medium"
          :class="mode === 'login' ? 'bg-primary text-white' : 'text-textSub'"
          @click="mode = 'login'"
        >
          登录
        </button>
        <button
          type="button"
          class="flex-1 px-4 py-1 rounded font-medium"
          :class="mode === 'register' ? 'bg-primary text-white' : 'text-textSub'"
          @click="mode = 'register'"
        >
          注册
        </button>
      </div>

      <div v-if="mode === 'login'" class="space-y-4">
        <div>
          <label class="block text-xs text-textSub mb-1">用户名</label>
          <input
            v-model="username"
            type="text"
            class="h-9 w-full rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
            placeholder="请输入用户名"
            @keydown.enter.prevent="submitLogin"
          />
        </div>
        <div>
          <label class="block text-xs text-textSub mb-1">密码</label>
          <input
            v-model="password"
            type="password"
            class="h-9 w-full rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
            placeholder="请输入密码"
            @keydown.enter.prevent="submitLogin"
          />
        </div>
        <button
          type="button"
          class="w-full h-9 rounded bg-primary text-white text-sm font-medium disabled:opacity-50"
          :disabled="isSubmitting"
          @click="submitLogin"
        >
          {{ isSubmitting ? '登录中...' : '登录' }}
        </button>
      </div>

      <div v-else class="space-y-4">
        <div>
          <label class="block text-xs text-textSub mb-1">用户名</label>
          <input
            v-model="registerUsername"
            type="text"
            class="h-9 w-full rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
            placeholder="请输入用户名"
          />
        </div>
        <div>
          <label class="block text-xs text-textSub mb-1">手机号</label>
          <input
            v-model="registerPhone"
            type="text"
            class="h-9 w-full rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
            placeholder="请输入手机号"
          />
        </div>
        <div>
          <label class="block text-xs text-textSub mb-1">邮箱（可选）</label>
          <input
            v-model="registerEmail"
            type="text"
            class="h-9 w-full rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
            placeholder="请输入邮箱"
          />
        </div>
        <div>
          <label class="block text-xs text-textSub mb-1">密码</label>
          <input
            v-model="registerPassword"
            type="password"
            class="h-9 w-full rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
            placeholder="请输入密码"
          />
        </div>
        <div>
          <label class="block text-xs text-textSub mb-1">确认密码</label>
          <input
            v-model="registerConfirmPassword"
            type="password"
            class="h-9 w-full rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
            placeholder="请再次输入密码"
            @keydown.enter.prevent="submitRegister"
          />
        </div>
        <button
          type="button"
          class="w-full h-9 rounded bg-primary text-white text-sm font-medium disabled:opacity-50"
          :disabled="isSubmitting"
          @click="submitRegister"
        >
          {{ isSubmitting ? '注册中...' : '注册' }}
        </button>
      </div>
    </div>
  </div>
</template>
