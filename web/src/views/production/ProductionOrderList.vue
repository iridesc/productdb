<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showMessage } from '@/utils/request'
import { getProductionOrders } from '@/api/production'
import type { ProductionOrder } from '@/types/production'
import { handleError } from '@/utils/request'
import { previewImage } from '@/utils/image'
import { formatNumber } from '@/utils/number'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const list = ref<ProductionOrder[]>([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })

const canManageProduction = computed(() => userStore.hasPermission('can_manage_production'))
const canCreate = computed(() => userStore.hasPermission('can_create_production'))

const statusMap: Record<string, string> = {
  draft: '草稿',
  pending: '待生产',
  in_production: '生产中',
  completed: '已完成',
  cancelled: '已取消'
}

const statusColor: Record<string, string> = {
  draft: '#909399',
  pending: '#e6a23c',
  in_production: '#fa8c16',
  completed: '#52c41a',
  cancelled: '#ff4d4f'
}

async function fetchList() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.value.page,
      page_size: pagination.value.page_size
    }
    const res: any = await getProductionOrders(params)
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
    <template v-if="canManageProduction">
    <van-nav-bar title="生产订单" left-arrow @click-left="router.back()">
      <template #right>
        <van-icon v-if="canCreate" name="plus" size="18" @click="goCreate" />
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
                <th>产品图片</th>
                <th>产品型号</th>
                <th>产品名称</th>
                <th>数量</th>
                <th>备注</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in list" :key="item.id" @click="goDetail(item.id)">
                <td class="order-no-cell">{{ item.order_no }}</td>
                <td>
                  <span class="status-tag"
                    :style="{ background: statusColor[item.status] + '20', color: statusColor[item.status] }">
                    {{ statusMap[item.status] || item.status }}
                  </span>
                </td>
                <td class="product-img-cell">
                  <img
                    v-if="item.product?.thumbnail_url"
                    :src="item.product.thumbnail_url"
                    class="product-thumb"
                    @click.stop="previewImage(item.product.thumbnail_url)"
                  />
                  <span v-else class="no-img">—</span>
                </td>
                <td class="code-cell">{{ item.product?.code || '—' }}</td>
                <td>{{ item.product?.name || '—' }}</td>
                <td class="center-cell">{{ formatNumber(item.quantity) }}</td>
                <td class="remark-cell">{{ item.remark || '—' }}</td>
                <td>{{ item.created_at?.slice(0, 10) }}</td>
              </tr>
            </tbody>
          </table>

          <van-empty v-if="!loading && list.length === 0" description="暂无订单" />
        </div>
      </van-pull-refresh>
      <van-pagination
        v-if="pagination.total > pagination.page_size"
        v-model="pagination.page"
        :total-items="pagination.total"
        :items-per-page="pagination.page_size"
        @change="fetchList"
      />
      <div v-if="pagination.total > pagination.page_size" style="text-align:center;color:#999;font-size:12px;padding:8px">
        共 {{ pagination.total }} 条
      </div>
    </div>
    </template>
    <van-empty v-else description="暂无权限，请联系管理员" />
  </div>
</template>

<style scoped>
.production-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.table-container {
  padding: 0 16px 16px;
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
  border-bottom: 2px solid #ddd;
  font-size: 13px;
}

.order-table td {
  padding: 14px 10px;
  border-bottom: 1px solid #ebebeb;
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

.order-table tbody tr:hover td {
  color: #1a1a1a;
}

.order-table tbody tr:last-child td {
  border-bottom: none;
}

.order-no-cell {
  font-weight: 600;
  color: #333;
}

.center-cell {
  text-align: left;
}

.status-tag {
  display: inline-block;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 4px;
}

.product-img-cell {
  text-align: left;
}

.product-thumb {
  width: 36px;
  height: 36px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #eee;
  display: inline-block;
  vertical-align: middle;
}

.no-img {
  color: #ccc;
  font-size: 12px;
}

.code-cell {
  font-size: 13px;
  color: #333;
  font-family: monospace;
  font-weight: 500;
}

.remark-cell {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #999;
  font-size: 12px;
}
</style>
