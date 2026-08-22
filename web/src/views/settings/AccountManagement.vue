<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showToast, showSuccessToast, showConfirmDialog } from 'vant'
import { useRouter } from 'vue-router'
import { getUsers, createUser, updateUser, deleteUser, updatePassword } from '@/api/user'
import type { User, UserCreate, UserUpdate } from '@/types/user'
import { showMessage } from '@/utils/request'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const isSuperuser = computed(() => userStore.userInfo?.is_superuser === true)
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
  can_manage_users: false,
  can_create_sales: false,
  can_create_production: false
})

const editFormData = ref<UserUpdate>({
  username: '',
  is_active: true,
  is_superuser: false,
  can_manage_materials: true,
  can_manage_sales: true,
  can_manage_production: true,
  can_manage_inventory: true,
  can_manage_users: false,
  can_create_sales: false,
  can_create_production: false
})

const passwordData = ref({
  password: '',
  confirmPassword: ''
})

// 编辑弹窗中的密码修改（选填）
const editPasswordData = ref({
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
    can_manage_users: false,
    can_create_sales: false,
    can_create_production: false
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
    can_manage_users: user.can_manage_users,
    can_create_sales: user.can_create_sales,
    can_create_production: user.can_create_production
  }
  editPasswordData.value = { password: '', confirmPassword: '' }
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
    // 如果填写了新密码，先校验再修改
    if (editPasswordData.value.password) {
      if (editPasswordData.value.password.length < 6) {
        showMessage('密码长度不能少于6位')
        return
      }
      if (editPasswordData.value.password !== editPasswordData.value.confirmPassword) {
        showMessage('两次输入的密码不一致')
        return
      }
      await updatePassword(currentUser.value.id, editPasswordData.value.password)
    }

    await updateUser(currentUser.value.id, editFormData.value)
    showSuccessToast('更新成功')
    showEditPopup.value = false
    loadUsers()
  } catch (error) {
    console.error('更新用户失败:', error)
  }
}

async function handleDelete(user: User) {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除用户「${user.username}」吗？此操作不可恢复。`,
      confirmButtonText: '删除',
      confirmButtonColor: '#ee0a24'
    })
    await deleteUser(user.id)
    showSuccessToast('删除成功')
    loadUsers()
  } catch (error) {
    // 用户取消或删除失败
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
    }
  }
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

async function handleLogout() {
  try {
    await showConfirmDialog({
      title: '提示',
      message: '确定要退出登录吗？'
    })
    userStore.logout()
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<template>
  <div class="account-management">
    <van-nav-bar title="我的" left-arrow @click-left="$router.back()" />

    <!-- 个人信息卡片 -->
    <div class="profile-card">
      <div class="profile-header">
        <div class="profile-avatar">
          <van-icon name="contact" size="44" color="#fff" />
        </div>
        <div class="profile-info">
          <div class="profile-name">{{ userStore.userInfo?.username || '-' }}</div>
          <div class="profile-meta">
            <van-tag v-if="userStore.userInfo?.is_superuser" type="warning" size="small">超级管理员</van-tag>
            <van-tag v-else type="primary" size="small">普通用户</van-tag>
            <span class="profile-status">
              <span class="status-dot" :class="{ active: userStore.userInfo?.is_active }"></span>
              {{ userStore.userInfo?.is_active ? '正常' : '已禁用' }}
            </span>
          </div>
        </div>
      </div>
      <div class="profile-permissions">
        <span v-if="userStore.userInfo?.can_manage_materials" class="perm-item">物料管理</span>
        <span v-if="userStore.userInfo?.can_manage_sales" class="perm-item">销售订单</span>
        <span v-if="userStore.userInfo?.can_manage_production" class="perm-item">生产订单</span>
      </div>
    </div>

    <!-- 用户管理 — 仅超级管理员可见 -->
    <template v-if="isSuperuser">
      <van-cell-group inset class="system-tools">
        <van-cell title="系统 Token 管理" label="管理 MCP 等系统集成凭证" is-link to="/system-tokens">
          <template #icon><van-icon name="key-o" class="system-tool-icon" /></template>
        </van-cell>
      </van-cell-group>
      <div class="section-header">
        <span class="section-title">用户管理</span>
        <span class="section-count">{{ users.length }} 个账号</span>
      </div>
      <div class="user-list">
        <van-pull-refresh v-model="loading" @refresh="loadUsers">
          <van-loading v-if="loading && users.length === 0" class="loading" />
          <van-empty v-else-if="!loading && users.length === 0" description="暂无账号" />
          <div v-else class="user-cards">
            <div
              v-for="user in users"
              :key="user.id"
              class="user-card"
              :class="{ 'is-self': user.id === userStore.userInfo?.id }"
            >
              <div class="user-card-main">
                <div class="user-avatar">
                  <van-icon name="contact" size="24" color="#1989fa" />
                </div>
                <div class="user-detail">
                  <div class="user-name">
                    {{ user.username }}
                    <span v-if="user.id === userStore.userInfo?.id" class="self-tag">我</span>
                  </div>
                  <div class="user-tags">
                    <van-tag :type="user.is_active ? 'success' : 'danger'" size="mini">
                      {{ user.is_active ? '启用' : '禁用' }}
                    </van-tag>
                    <van-tag v-if="user.is_superuser" type="warning" size="mini">管理员</van-tag>
                  </div>
                </div>
              </div>
              <div class="user-card-actions">
                <van-button size="mini" plain type="primary" icon="edit" @click="openEditDialog(user)">编辑</van-button>
                <van-button size="mini" plain type="success" icon="lock" @click="openPasswordDialog(user)">密码</van-button>
                <van-button
                  v-if="user.id !== userStore.userInfo?.id"
                  size="mini" plain type="danger" icon="delete-o"
                  @click="handleDelete(user)"
                >删除</van-button>
              </div>
            </div>
          </div>
        </van-pull-refresh>
      </div>

      <!-- 新增按钮 -->
      <div class="add-user-bar">
        <van-button type="primary" block round @click="openCreateDialog">
          <van-icon name="plus" size="18" />新增账号
        </van-button>
      </div>
    </template>

    <!-- 退出登录 -->
    <div class="logout-section">
      <van-button type="danger" plain round block @click="handleLogout">退出登录</van-button>
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
            <van-cell title="可创建销售订单" center>
              <template #right-icon>
                <van-switch v-model="formData.can_create_sales" />
              </template>
            </van-cell>
            <van-cell title="可创建生产订单" center>
              <template #right-icon>
                <van-switch v-model="formData.can_create_production" />
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
          <div class="permission-title">修改密码（选填，不填则不修改）</div>
          <van-cell-group inset>
            <van-field
              v-model="editPasswordData.password"
              label="新密码"
              placeholder="至少6位，留空则不修改"
              type="password"
            />
            <van-field
              v-model="editPasswordData.confirmPassword"
              label="确认密码"
              placeholder="请再次输入新密码"
              type="password"
            />
          </van-cell-group>
        </div>

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
            <van-cell title="可创建销售订单" center>
              <template #right-icon>
                <van-switch v-model="editFormData.can_create_sales!" />
              </template>
            </van-cell>
            <van-cell title="可创建生产订单" center>
              <template #right-icon>
                <van-switch v-model="editFormData.can_create_production!" />
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
  padding-bottom: 30px;
}

/* ====== 个人信息卡片 ====== */
.profile-card {
  background: linear-gradient(135deg, #1989fa 0%, #36b1ff 100%);
  margin: 16px;
  border-radius: 16px;
  padding: 20px;
  color: #fff;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
}

.profile-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.profile-info {
  flex: 1;
  min-width: 0;
}

.profile-name {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 6px;
}

.profile-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.profile-status {
  font-size: 12px;
  opacity: 0.85;
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff976a;
}
.status-dot.active {
  background: #07c160;
}

.profile-permissions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.perm-item {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.18);
  padding: 3px 10px;
  border-radius: 20px;
  white-space: nowrap;
}

/* ====== 区域头部 ====== */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 16px 10px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
}

.section-count {
  font-size: 13px;
  color: #999;
}

/* ====== 用户列表 ====== */
.user-list {
  padding: 0 16px;
}

.user-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.user-card.is-self {
  border: 1px solid #dbeafe;
  background: #f0f7ff;
}

.user-card-main {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e8f2ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-detail {
  min-width: 0;
}

.user-name {
  font-size: 15px;
  font-weight: 500;
  color: #323233;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.self-tag {
  font-size: 10px;
  color: #1989fa;
  background: #e8f2ff;
  padding: 1px 6px;
  border-radius: 8px;
  font-weight: 400;
}

.user-tags {
  display: flex;
  gap: 4px;
}

.user-card-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

/* ====== 新增按钮 ====== */
.add-user-bar {
  padding: 16px;
}

/* ====== 退出登录 ====== */
.logout-section {
  padding: 8px 16px 24px;
}

/* ====== 通用 ====== */
.loading {
  display: flex;
  justify-content: center;
  padding: 50px 0;
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
