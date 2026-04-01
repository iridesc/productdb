<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showMessage } from '@/utils/request'
import { useUserStore } from '@/store/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(true)

// 检查登录状态
onMounted(async () => {
  const token = localStorage.getItem('token')
  if (token) {
    userStore.setToken(token)
  }
  loading.value = false
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else {
    next()
  }
})
</script>

<template>
  <div id="app">
    <router-view v-if="!loading" />
    <div v-else class="loading">
      <van-loading type="spinner" size="48px">加载中...</van-loading>
    </div>
  </div>
</template>

<style scoped>
.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f5f5f5;
}
</style>