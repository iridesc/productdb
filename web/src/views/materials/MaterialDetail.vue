<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { getMaterial, deleteMaterial } from '@/api/material'
import type { Material } from '@/types/material'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref<Material | null>(null)
const id = route.params.id as string

const categoryMap: Record<string, string> = {
  finished_product: '成品',
  semi_finished: '半成品',
  raw_material: '原材料',
  auxiliary: '辅料'
}

async function fetchDetail() {
  loading.value = true
  try {
    detail.value = await getMaterial(id) as any
  } catch (e: any) {
    showToast(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete() {
  await showConfirmDialog({
    title: '确认删除',
    message: '确定要删除这个物料吗？'
  })
  
  try {
    await deleteMaterial(id)
    showToast('删除成功')
    router.back()
  } catch (e: any) {
    showToast(e.message || '删除失败')
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="material-detail-page">
    <van-nav-bar title="物料详情" left-arrow @click-left="router.back()" />

    <div v-if="detail" class="detail-content">
      <!-- 基本信息 -->
      <div class="card">
        <div class="card-title">基本信息</div>
        <div class="info-row">
          <span class="label">编码</span>
          <span class="value">{{ detail.code }}</span>
        </div>
        <div class="info-row">
          <span class="label">名称</span>
          <span class="value">{{ detail.name }}</span>
        </div>
        <div class="info-row">
          <span class="label">分类</span>
          <span class="value">{{ categoryMap[detail.category] || detail.category }}</span>
        </div>
        <div class="info-row">
          <span class="label">单位</span>
          <span class="value">{{ detail.unit }}</span>
        </div>
        <div class="info-row">
          <span class="label">规格</span>
          <span class="value">{{ detail.specification || '-' }}</span>
        </div>
        <div class="info-row">
          <span class="label">单价</span>
          <span class="value">¥{{ detail.price }}</span>
        </div>
      </div>

      <!-- 库存信息 -->
      <div class="card">
        <div class="card-title">库存信息</div>
        <div class="info-row">
          <span class="label">当前库存</span>
          <span class="value" :class="{ 'low-stock': detail.current_stock < detail.safety_stock }">
            {{ detail.current_stock }} {{ detail.unit }}
          </span>
        </div>
        <div class="info-row">
          <span class="label">安全库存</span>
          <span class="value">{{ detail.safety_stock }} {{ detail.unit }}</span>
        </div>
      </div>

      <!-- 描述 -->
      <div v-if="detail.description" class="card">
        <div class="card-title">描述</div>
        <div class="description">{{ detail.description }}</div>
      </div>

      <!-- 操作 -->
      <div class="action-btns">
        <van-button type="danger" block @click="handleDelete">删除物料</van-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.material-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.detail-content {
  padding: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}

.info-row:last-child {
  border-bottom: none;
}

.label {
  color: #999;
  font-size: 14px;
}

.value {
  color: #333;
  font-size: 14px;
}

.value.low-stock {
  color: #ff4d4f;
}

.description {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

.action-btns {
  padding: 16px;
}
</style>