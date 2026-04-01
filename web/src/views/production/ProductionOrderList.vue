<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showMessage } from '@/utils/request'
import { getProductionOrders } from '@/api/production'
import type { ProductionOrder } from '@/types/production'
import { handleError } from '@/utils/request'

const router = useRouter()
const loading = ref(false)
const list = ref<ProductionOrder[]>([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })

const statusMap: Record<string, string> = {
  pending: '待生产',
  in_production: '生产中',
  completed: '已完成',
  cancelled: '已取消'
}

const statusColor: Record<string, string> = {
  pending: '#999',
  in_production: '#fa8c16',
  completed: '#52c41a',
  cancelled: '#ff4d4f'
}

async function fetchList() {
  loading.value = true
  try {
    const res: any = await getProductionOrders({
      page: pagination.value.page,
      page_size: pagination.value.page_size
    })
    list.value = res.items
    pagination.value.total = res.total
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    loading.value = false
  }
}

function goCreate() {
  router.push('/production-orders/create')
}

function goDetail(id: string) {
  router.push(`/production-orders/${id}`)
}

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="production-page">
    <van-nav-bar title="生产订单" left-arrow @click-left="router.back()">
      <template #right>
        <van-icon name="plus" size="18" @click="goCreate" />
      </template>
    </van-nav-bar>

    <div class="table-container">
      <van-pull-refresh v-model="loading" @refresh="fetchList">
        <div class="table-wrapper">
          <table class="order-table">
            <thead>
              <tr>
                <th>订单号</th>
                <th>状态</th>
                <th>产品名称</th>
                <th>数量</th>
                <th>物料种类</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in list" :key="item.id" @click="goDetail(item.id)">
                <td class="order-no-cell">{{ item.order_no }}</td>
                <td>
                  <span class="status-tag"
                    :style="{ background: statusColor[item.status] + '20', color: statusColor[item.status] }">
                    {{ statusMap[item.status] }}
                  </span>
                </td>
                <td>{{ item.product_name }}</td>
                <td class="center-cell">{{ item.quantity }}</td>
                <td class="center-cell">{{ item.items?.length || 0 }} 种</td>
                <td>{{ item.created_at?.slice(0, 10) }}</td>
              </tr>
            </tbody>
          </table>

          <van-empty v-if="!loading && list.length === 0" description="暂无订单" />
        </div>
      </van-pull-refresh>
    </div>
  </div>
</template>

<style scoped>
.production-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.table-container {
  padding: 16px;
}

.table-wrapper {
  background: #fff;
  border-radius: 8px;
  overflow-x: auto;
}

.order-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  white-space: nowrap;
}

.order-table thead {
  background: #fafafa;
}

.order-table th {
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  color: #666;
  border-bottom: 2px solid #eee;
  font-size: 13px;
}

.order-table td {
  padding: 14px 10px;
  border-bottom: 1px solid #f5f5f5;
  color: #333;
  vertical-align: middle;
}

.order-table tbody tr {
  cursor: pointer;
  transition: background-color 0.2s;
}

.order-table tbody tr:hover {
  background: #f8f9ff;
}

.order-table tbody tr:last-child td {
  border-bottom: none;
}

.order-no-cell {
  font-weight: 600;
  color: #1989fa;
}

.center-cell {
  text-align: center;
}

.status-tag {
  display: inline-block;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 4px;
}
</style>
