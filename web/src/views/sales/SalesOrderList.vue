<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getSalesOrders } from '@/api/sales'
import type { SalesOrder } from '@/types/sales'

const router = useRouter()
const loading = ref(false)
const list = ref<SalesOrder[]>([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })

const statusMap: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消'
}

const statusColor: Record<string, string> = {
  draft: '#999',
  published: '#1989fa',
  in_progress: '#fa8c16',
  completed: '#52c41a',
  cancelled: '#ff4d4f'
}

async function fetchList() {
  loading.value = true
  try {
    const res: any = await getSalesOrders({
      page: pagination.value.page,
      page_size: pagination.value.page_size
    })
    list.value = res.items
    pagination.value.total = res.total
  } catch (e: any) {
    showToast(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function goCreate() {
  router.push('/sales-orders/create')
}

function goDetail(id: string) {
  router.push(`/sales-orders/${id}`)
}

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="sales-page">
    <van-nav-bar title="销售订单" left-arrow @click-left="router.back()" />

    <div class="list-container">
      <van-pull-refresh v-model="loading" @refresh="fetchList">
        <div 
          v-for="item in list" 
          :key="item.id" 
          class="list-item"
          @click="goDetail(item.id)"
        >
          <div class="item-header">
            <span class="order-no">{{ item.order_no }}</span>
            <span 
              class="status-tag" 
              :style="{ background: statusColor[item.status] + '20', color: statusColor[item.status] }"
            >
              {{ statusMap[item.status] }}
            </span>
          </div>
          <div class="item-body">
            <div class="item-row">
              <span class="label">客户</span>
              <span class="value">{{ item.customer_name }}</span>
            </div>
            <div class="item-row">
              <span class="label">快递单号</span>
              <span class="value">{{ item.express_no || '-' }}</span>
            </div>
            <div class="item-row">
              <span class="label">金额</span>
              <span class="value price">¥{{ item.total_amount }}</span>
            </div>
          </div>
          <div class="item-footer">
            <span class="item-count">{{ item.items?.length || 0 }} 个商品</span>
            <span class="item-time">{{ item.created_at?.slice(0, 10) }}</span>
          </div>
        </div>

        <van-empty v-if="!loading && list.length === 0" description="暂无订单" />
      </van-pull-refresh>
    </div>

    <van-button
      type="primary"
      size="large"
      block
      class="add-btn"
      @click="goCreate"
    >
      新建订单
    </van-button>
  </div>
</template>

<style scoped>
.sales-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 70px;
}

.list-container {
  padding: 16px;
}

.list-item {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.order-no {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.status-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 4px;
}

.item-body {
  margin-bottom: 12px;
}

.item-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
}

.label {
  color: #999;
  font-size: 13px;
}

.value {
  color: #333;
  font-size: 13px;
}

.value.price {
  color: #ff4d4f;
  font-weight: 600;
}

.item-footer {
  display: flex;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid #f5f5f5;
  font-size: 12px;
  color: #999;
}

.add-btn {
  position: fixed;
  bottom: 20px;
  left: 16px;
  right: 16px;
  z-index: 100;
}
</style>