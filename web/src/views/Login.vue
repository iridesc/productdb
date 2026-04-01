<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { useUserStore } from '@/store/user'
import request from '@/utils/request'
import { handleError } from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    showToast('请输入用户名和密码')
    return
  }
  
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)
    const res: any = await request.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    userStore.setToken(res.access_token)
    showToast('登录成功')
    router.replace('/dashboard')
  } catch (e) {
    const errorMessage = handleError(e)
    showToast(errorMessage)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-header">
      <h1>ERP 管理系统</h1>
      <p>物料生产管理</p>
    </div>
    
    <van-form @submit="handleLogin" class="login-form">
      <van-cell-group inset>
        <van-field
          v-model="username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          :rules="[{ required: true, message: '请输入用户名' }]"
        />
        <van-field
          v-model="password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请输入密码' }]"
        />
      </van-cell-group>
      
      <div class="login-btn">
        <van-button
          type="primary"
          size="large"
          :loading="loading"
          native-type="submit"
        >
          登录
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  background: #fff;
  padding: 60px 24px;
}

.login-header {
  text-align: center;
  margin-bottom: 48px;
}

.login-header h1 {
  font-size: 24px;
  color: #333;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 14px;
  color: #999;
}

.login-btn {
  margin: 24px 16px;
}
</style>