<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const active = ref(0)

const tabItems = [
  { icon: 'orders-o', path: '/sales-orders', text: '销售' },
  { icon: 'friends-o', path: '/production-orders', text: '生产' },
  { icon: 'bag-o', path: '/materials', text: '物料' },
  { icon: 'user-o', path: '/accounts', text: '账号' }
]

watch(() => route.path, (path) => {
  const index = tabItems.findIndex(item => path.startsWith(item.path))
  if (index !== -1) {
    active.value = index
  }
}, { immediate: true })

function handleChange(index: number) {
  router.push(tabItems[index].path)
}
</script>

<template>
  <van-tabbar v-model="active" @change="handleChange">
    <van-tabbar-item 
      v-for="(item, index) in tabItems" 
      :key="index"
      :icon="item.icon"
    >
      {{ item.text }}
    </van-tabbar-item>
  </van-tabbar>
</template>
