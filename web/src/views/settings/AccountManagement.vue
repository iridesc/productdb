<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast, showSuccessToast, showDialog } from 'vant'
import { useRouter } from 'vue-router'
import { getUsers, createUser, updateUser, deleteUser, updatePassword } from '@/api/user'
import type { User, UserCreate, UserUpdate } from '@/types/user'
import { showMessage } from '@/utils/request'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const users = ref<User[]>([])
const loading = ref(false)
const showCreatePopup = ref(false)
const showEditPopup = ref(false)
const showPasswordPopup = ref(false)
const currentUser = ref<User | null>(null)

const formData = ref<UserCreate>({
  username: '',
  password: '',
  can_manage_materials: true,
  can_manage_sales: true,
  can_manage_production: true,
  can_manage_inventory: true,
  can_manage_users: false
})

const editFormData = ref<UserUpdate>({
  username: '',
  is_active: true,
  is_superuser: false,
  can_manage_materials: true,
  can_manage_sales: true,
  can_manage_production: true,
  can_manage_inventory: true,
  can_manage_users: false
})

const passwordData = ref({
  password: '',
  confirmPassword: ''
})

onMounted(() => {
  loadUsers()
})

async function loadUsers() {
  loading.value = true
  try {
    users.value = await getUsers()
  } catch (error) {
    console.error('加载用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  formData.value = {
    username: '',
    password: '',
    can_manage_materials: true,
    can_manage_sales: true,
    can_manage_production: true,
    can_manage_inventory: true,
    can_manage_users: false
  }
  showCreatePopup.value = true
}

function openEditDialog(user: User) {
  currentUser.value = user
  editFormData.value = {
    username: user.username,
    is_active: user.is_active,
    is_superuser: user.is_superuser,
    can_manage_materials: user.can_manage_materials,
    can_manage_sales: user.can_manage_sales,
    can_manage_production: user.can_manage_production,
    can_manage_inventory: user.can_manage_inventory,
    can_manage_users: user.can_manage_users
  }
  showEditPopup.value = true
}

function openPasswordDialog(user: User) {
  currentUser.value = user
  passwordData.value = {
    password: '',
    confirmPassword: ''
  }
  showPasswordPopup.value = true
}

async function handleCreate() {
  if (!formData.value.username || !formData.value.password) {
    showMessage('请填写完整信息')
    return
  }

  try {
    await createUser(formData.value)
    showSuccessToast('创建成功')
    showCreatePopup.value = false
    loadUsers()
  } catch (error) {
    console.error('创建用户失败:', error)
  }
}

async function handleEdit() {
  if (!currentUser.value) return

  try {
    await updateUser(currentUser.value.id, editFormData.value)
    showSuccessToast('更新成功')
    showEditPopup.value = false
    loadUsers()
  } catch (error) {
    console.error('更新用户失败:', error)
  }
}

async function handleDelete(user: User) {
  showDialog({
    title: '确认删除',
    message: `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
    showCancelButton: true,
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    confirmButtonColor: '#ee0a24'
  }).then(async () => {
    try {
      await deleteUser(user.id)
      showSuccessToast('删除成功')
      loadUsers()
    } catch (error) {
      console.error('删除用户失败:', error)
    }
  })
}

async function handleChangePassword() {
  if (!currentUser.value) return

  if (passwordData.value.password.length < 6) {
    showMessage('密码长度不能少于6位')
    return
  }

  if (passwordData.value.password !== passwordData.value.confirmPassword) {
    showMessage('两次输入的密码不一致')
    return
  }

  try {
    await updatePassword(currentUser.value.id, passwordData.value.password)
    showSuccessToast('密码修改成功')
    showPasswordPopup.value = false
  } catch (error) {
    console.error('修改密码失败:', error)
  }
}

function handleLogout() {
  showDialog({
    title: '提示',
    message: '确定要退出登录吗？',
    showCancelButton: true,
    confirmButtonText: '确定',
    cancelButtonText: '取消'
  }).then(() => {
    userStore.logout()
    router.push('/login')
  })
}
</script>

<template>
  <div class="account-management">
    <van-nav-bar
      title="账号管理"
      left-arrow
      @click-left="$router.back()"
    >
      <template #right>
        <van-icon name="close" size="18" @click="handleLogout" style="margin-right: 8px;" />
        <van-icon name="plus" size="20" @click="openCreateDialog" />
      </template>
    </van-nav-bar>

    <div class="content">
      <van-pull-refresh v-model="loading" @refresh="loadUsers">
        <van-loading v-if="loading && users.length === 0" class="loading" />
        
        <van-empty v-else-if="!loading && users.length === 0" description="暂无账号" />
        
        <van-cell-group v-else inset>
          <van-cell
            v-for="user in users"
            :key="user.id"
            :title="user.username"
            label=" "
          >
            <template #icon>
              <van-icon name="contact" size="24" style="margin-right: 10px; line-height: inherit;" />
            </template>
            <template #value>
              <div class="user-actions">
                <van-tag :type="user.is_active ? 'success' : 'danger'" size="small">
                  {{ user.is_active ? '启用' : '禁用' }}
                </van-tag>
                <van-tag v-if="user.is_superuser" type="warning" size="small" style="margin-left: 4px;">
                  管理员
                </van-tag>
              </div>
            </template>
            <template #right-icon>
              <div class="action-buttons">
                <van-icon
                  name="edit"
                  size="18"
                  color="#1989fa"
                  @click.stop="openEditDialog(user)"
                  style="margin-right: 12px;"
                />
                <van-icon
                  name="lock"
                  size="18"
                  color="#07c160"
                  @click.stop="openPasswordDialog(user)"
                  style="margin-right: 12px;"
                />
                <van-icon
                  name="delete-o"
                  size="18"
                  color="#ee0a24"
                  @click.stop="handleDelete(user)"
                />
              </div>
            </template>
          </van-cell>
        </van-cell-group>
      </van-pull-refresh>
    </div>

    <!-- 新增用户弹窗 -->
    <van-popup
      v-model:show="showCreatePopup"
      position="bottom"
      round
      :style="{ height: '85%' }"
    >
      <div class="popup-header">
        <h3>新增账号</h3>
      </div>
      <van-form @submit="handleCreate">
        <van-cell-group inset>
          <van-field
            v-model="formData.username"
            label="用户名"
            placeholder="请输入用户名"
            :rules="[{ required: true, message: '请填写用户名' }]"
          />
          <van-field
            v-model="formData.password"
            label="密码"
            placeholder="请输入密码（至少6位）"
            type="password"
            :rules="[{ required: true, message: '请填写密码' }]"
          />
        </van-cell-group>

        <div class="permission-section">
          <div class="permission-title">模块权限</div>
          <van-cell-group inset>
            <van-cell title="物料管理" center>
              <template #right-icon>
                <van-switch v-model="formData.can_manage_materials" />
              </template>
            </van-cell>
            <van-cell title="销售订单" center>
              <template #right-icon>
                <van-switch v-model="formData.can_manage_sales" />
              </template>
            </van-cell>
            <van-cell title="生产订单" center>
              <template #right-icon>
                <van-switch v-model="formData.can_manage_production" />
              </template>
            </van-cell>
            <van-cell title="库存管理" center>
              <template #right-icon>
                <van-switch v-model="formData.can_manage_inventory" />
              </template>
            </van-cell>
            <van-cell title="用户管理" center>
              <template #label>
                <span style="font-size: 12px; color: #999;">（仅管理员可用）</span>
              </template>
              <template #right-icon>
                <van-switch v-model="formData.can_manage_users" />
              </template>
            </van-cell>
          </van-cell-group>
        </div>

        <div class="popup-footer">
          <van-button round block type="primary" native-type="submit">
            确认创建
          </van-button>
        </div>
      </van-form>
    </van-popup>

    <!-- 编辑用户弹窗 -->
    <van-popup
      v-model:show="showEditPopup"
      position="bottom"
      round
      :style="{ height: '85%' }"
    >
      <div class="popup-header">
        <h3>编辑账号</h3>
      </div>
      <van-form @submit="handleEdit">
        <van-cell-group inset>
          <van-field
            v-model="editFormData.username"
            label="用户名"
            placeholder="请输入用户名"
            :rules="[{ required: true, message: '请填写用户名' }]"
          />
          <van-cell title="状态" center>
            <template #right-icon>
              <van-switch v-model="editFormData.is_active!" />
            </template>
          </van-cell>
          <van-cell title="管理员权限" center>
            <template #right-icon>
              <van-switch v-model="editFormData.is_superuser!" />
            </template>
          </van-cell>
        </van-cell-group>

        <div class="permission-section">
          <div class="permission-title">模块权限</div>
          <van-cell-group inset>
            <van-cell title="物料管理" center>
              <template #right-icon>
                <van-switch v-model="editFormData.can_manage_materials!" />
              </template>
            </van-cell>
            <van-cell title="销售订单" center>
              <template #right-icon>
                <van-switch v-model="editFormData.can_manage_sales!" />
              </template>
            </van-cell>
            <van-cell title="生产订单" center>
              <template #right-icon>
                <van-switch v-model="editFormData.can_manage_production!" />
              </template>
            </van-cell>
            <van-cell title="库存管理" center>
              <template #right-icon>
                <van-switch v-model="editFormData.can_manage_inventory!" />
              </template>
            </van-cell>
            <van-cell title="用户管理" center>
              <template #label>
                <span style="font-size: 12px; color: #999;">（仅管理员可用）</span>
              </template>
              <template #right-icon>
                <van-switch v-model="editFormData.can_manage_users!" />
              </template>
            </van-cell>
          </van-cell-group>
        </div>

        <div class="popup-footer">
          <van-button round block type="primary" native-type="submit">
            保存修改
          </van-button>
        </div>
      </van-form>
    </van-popup>

    <!-- 修改密码弹窗 -->
    <van-popup
      v-model:show="showPasswordPopup"
      position="bottom"
      round
      :style="{ height: '50%' }"
    >
      <div class="popup-header">
        <h3>修改密码</h3>
      </div>
      <van-form @submit="handleChangePassword">
        <van-cell-group inset>
          <van-field
            v-model="passwordData.password"
            label="新密码"
            placeholder="请输入新密码（至少6位）"
            type="password"
            :rules="[{ required: true, message: '请填写新密码' }]"
          />
          <van-field
            v-model="passwordData.confirmPassword"
            label="确认密码"
            placeholder="请再次输入新密码"
            type="password"
            :rules="[{ required: true, message: '请再次输入密码' }]"
          />
        </van-cell-group>
        <div class="popup-footer">
          <van-button round block type="primary" native-type="submit">
            确认修改
          </van-button>
        </div>
      </van-form>
    </van-popup>
  </div>
</template>

<style scoped>
.account-management {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content {
  padding: 16px 0;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 50px 0;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-buttons {
  display: flex;
  align-items: center;
  margin-left: 8px;
}

.popup-header {
  padding: 16px;
  text-align: center;
  border-bottom: 1px solid #ebedf0;
}

.popup-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.popup-footer {
  padding: 16px;
}

.permission-section {
  margin-top: 16px;
}

.permission-title {
  font-size: 14px;
  font-weight: 500;
  color: #666;
  padding: 0 16px 8px 16px;
}
</style>
