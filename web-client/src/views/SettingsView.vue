<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  createUserAPI,
  deleteUserAPI,
  getUsersAPI,
  type UserProfile
} from '@/api/auth'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()

const userManageVisible = ref(false)
const usersLoading = ref(false)
const users = ref<UserProfile[]>([])
const creatingUser = ref(false)

const createForm = reactive({
  username: '',
  password: '',
  phone: '',
  email: ''
})

const canManageUsers = computed(() => authStore.hasPermission('user:manage'))

const userColumns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '用户名', dataIndex: 'username', key: 'username', width: 160 },
  { title: 'UID', dataIndex: 'uid', key: 'uid', width: 200 },
  { title: '手机号', dataIndex: 'phone', key: 'phone', width: 150 },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '操作', key: 'actions', width: 80, align: 'center' as const }
]

const resetCreateForm = () => {
  createForm.username = ''
  createForm.password = ''
  createForm.phone = ''
  createForm.email = ''
}

const loadUsers = async () => {
  if (!canManageUsers.value) return
  usersLoading.value = true
  try {
    users.value = await getUsersAPI(1, 100)
  } catch (error: any) {
    message.error(error?.response?.data?.detail || error?.message || '加载用户列表失败')
  } finally {
    usersLoading.value = false
  }
}

const openUserManager = async () => {
  if (!canManageUsers.value) {
    message.warning('当前账号无用户管理权限')
    return
  }
  userManageVisible.value = true
  await loadUsers()
}

const createUser = async () => {
  if (!createForm.username.trim() || !createForm.password.trim() || !createForm.phone.trim()) {
    message.warning('用户名、密码、手机号为必填')
    return
  }
  creatingUser.value = true
  try {
    await createUserAPI({
      username: createForm.username.trim(),
      password: createForm.password,
      phone: createForm.phone.trim(),
      email: createForm.email.trim() || undefined
    })
    message.success('用户创建成功')
    resetCreateForm()
    await loadUsers()
  } catch (error: any) {
    message.error(error?.response?.data?.detail || error?.message || '用户创建失败')
  } finally {
    creatingUser.value = false
  }
}

const deleteUser = (user: UserProfile) => {
  Modal.confirm({
    title: `删除用户 ${user.username}`,
    content: '删除后不可恢复，是否继续？',
    okText: '删除',
    okButtonProps: { danger: true },
    cancelText: '取消',
    onOk: async () => {
      try {
        await deleteUserAPI(user.id)
        message.success('删除成功')
        await loadUsers()
      } catch (error: any) {
        message.error(error?.response?.data?.detail || error?.message || '删除失败')
      }
    }
  })
}

onMounted(() => {
  if (canManageUsers.value) {
    void loadUsers()
  }
})
</script>

<template>
  <div class="min-h-screen bg-bgMain p-6">
    <div class="max-w-5xl mx-auto space-y-6">
      <section class="bg-card rounded-lg shadow-sm border border-border p-6">
        <h1 class="text-xl font-semibold text-textMain">设置</h1>
        <p class="text-sm text-textMute mt-1">账号与系统配置</p>
      </section>

      <section class="bg-card rounded-lg shadow-sm border border-border p-6">
        <div class="flex items-center justify-between gap-4">
          <div>
            <h2 class="text-base font-semibold text-textMain">用户管理</h2>
            <p class="text-xs text-textMute mt-1">非路由页面管理用户，支持新增与删除</p>
          </div>
          <button
            type="button"
            class="h-9 px-4 rounded bg-primary text-white text-sm font-medium disabled:opacity-50"
            :disabled="!canManageUsers"
            @click="openUserManager"
          >
            打开用户管理
          </button>
        </div>
        <p v-if="!canManageUsers" class="text-xs text-down mt-3">
          当前账号无 `user:manage` 权限，仅管理员可进行用户增删。
        </p>
      </section>
    </div>

    <a-modal
      v-model:open="userManageVisible"
      title="用户管理"
      width="980px"
      :footer="null"
      destroy-on-close
    >
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input
            v-model="createForm.username"
            type="text"
            placeholder="用户名 *"
            class="h-9 rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
          />
          <input
            v-model="createForm.password"
            type="password"
            placeholder="密码 *"
            class="h-9 rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
          />
          <input
            v-model="createForm.phone"
            type="text"
            placeholder="手机号 *"
            class="h-9 rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
          />
          <div class="flex gap-2">
            <input
              v-model="createForm.email"
              type="text"
              placeholder="邮箱（可选）"
              class="h-9 flex-1 rounded border border-border px-3 text-sm text-textMain bg-card focus:border-primary focus:outline-none"
            />
            <button
              type="button"
              class="h-9 px-3 rounded bg-primary text-white text-sm font-medium disabled:opacity-50"
              :disabled="creatingUser"
              @click="createUser"
            >
              新增
            </button>
          </div>
        </div>

        <a-table
          :columns="userColumns"
          :data-source="users"
          :loading="usersLoading"
          :pagination="{ pageSize: 10 }"
          :row-key="(record: UserProfile) => record.id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'actions'">
              <a-button
                type="text"
                danger
                size="small"
                @click="deleteUser(record)"
              >
                删除
              </a-button>
            </template>
          </template>
        </a-table>
      </div>
    </a-modal>
  </div>
</template>
