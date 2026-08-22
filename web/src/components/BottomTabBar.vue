<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const active = ref(0)

const allTabs = [
  { icon: 'orders-o', path: '/sales-orders', text: '销售', permission: 'can_manage_sales' },
  { icon: 'friends-o', path: '/production-orders', text: '生产', permission: 'can_manage_production' },
  { icon: 'bag-o', path: '/materials', text: '物料', permission: null },
  { icon: 'user-o', path: '/accounts', text: '我的', permission: null }
]

const tabItems = computed(() =>
  allTabs.filter(tab => {
    if (tab.permission) return userStore.hasPermission(tab.permission)
    return true
  })
)

watch(() => route.path, (path) => {
  const index = tabItems.value.findIndex(item => path.startsWith(item.path))
  if (index !== -1) {
    active.value = index
  }
}, { immediate: true })

function handleTabClick(index: number) {
  active.value = index
  router.push(tabItems.value[index].path)
}
</script>

<template>
  <van-tabbar :model-value="active" safe-area-inset-bottom>
    <van-tabbar-item
      v-for="(item, index) in tabItems"
      :key="index"
      :icon="item.icon"
      @click="handleTabClick(index)"
    >
      {{ item.text }}
    </van-tabbar-item>
  </van-tabbar>
</template>
