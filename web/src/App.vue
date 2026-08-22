<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import BottomTabBar from '@/components/BottomTabBar.vue'
import { useUserStore } from '@/store/user'

const route = useRoute()
const userStore = useUserStore()
const loading = ref(true)

const hideTabBar = computed(() => {
  const hiddenPaths = ['/login']
  return hiddenPaths.some(path => route.path.startsWith(path))
})

onMounted(async () => {
  userStore.loadUserInfo()
  loading.value = false
})
</script>

<template>
  <div id="app">
    <router-view v-if="!loading" />
    <BottomTabBar v-if="!loading && !hideTabBar" />
    <div v-else-if="loading" class="loading">
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

<style>
/* 图片预览不超出屏幕 */
.van-image-preview__image .van-image__img,
.van-image-preview__image > img {
  max-width: 90vw !important;
  max-height: 80vh !important;
  width: auto !important;
  height: auto !important;
}
</style>
