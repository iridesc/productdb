<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showDialog } from 'vant'
import { previewImage } from '@/utils/image'
import { showMessage } from '@/utils/request'
import { getSalesOrders } from '@/api/sales'
import type { SalesOrder } from '@/types/sales'
import { handleError } from '@/utils/request'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const hasPermission = computed(() => userStore.hasPermission('can_manage_sales'))
const canCreate = computed(() => userStore.hasPermission('can_create_sales'))
const loading = ref(false)
const list = ref<SalesOrder[]>([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })

const statusMap: Record<string, string> = {
  draft: '草稿',
  pending: '待处理',
  completed: '已完成',
  cancelled: '已取消'
}

const statusColor: Record<string, string> = {
  draft: '#666666',
  pending: '#fa8c16',
  completed: '#52c41a',
  cancelled: '#ff4d4f'
}

// 获取订单商品缩略图（最多4张）
function getOrderThumbnails(order: SalesOrder): string[] {
  const images: string[] = []
  if (order.items) {
    for (const item of order.items) {
      if (item.product?.thumbnail_url && images.length < 4) {
        images.push(item.product.thumbnail_url)
      }
    }
  }
  return images
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
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
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

function showFullText(title: string, text: string) {
  if (!text) return
  showDialog({ title, message: text, confirmButtonText: '关闭' })
}

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="sales-page">
    <template v-if="hasPermission">
    <van-nav-bar title="销售订单" left-arrow @click-left="router.back()">
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
                <th>商品数</th>
                <th>图片</th>
                <th>备注</th>
                <th>创建时间</th>
                <th>客户信息</th>
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
                <td class="center-cell">{{ item.items?.length || 0 }}</td>
                <td>
                  <div class="thumbnail-list">
                    <img v-for="(img, idx) in getOrderThumbnails(item)" :key="idx" :src="img" class="thumbnail-img" @click.stop="previewImage(img)" />
                    <span v-if="!getOrderThumbnails(item).length" class="no-image">-</span>
                  </div>
                </td>
                <td class="text-ellipsis" @click.stop="showFullText('备注', item.remark)">{{ item.remark || '-' }}</td>
                <td>{{ item.created_at?.slice(0, 10) }}</td>
                <td class="text-ellipsis" @click.stop="showFullText('客户信息', item.customer_info)">{{ item.customer_info || '-' }}</td>
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
.sales-page {
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
  -webkit-overflow-scrolling: touch;
}

.order-table {
  width: 100%;
  min-width: 600px;
  border-collapse: collapse;
  font-size: 13px;
}

.order-table thead {
  background: #fafafa;
}

.order-table th {
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  color: #666;
  border-bottom: 2px solid #eee;
  font-size: 13px;
  white-space: nowrap;
}

.order-table td {
  padding: 12px 8px;
  border-bottom: 1px solid #f5f5f5;
  color: #333;
  vertical-align: middle;
  white-space: nowrap;
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
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.price-cell {
  color: #ff4d4f;
  font-weight: 600;
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

.thumbnail-list {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.thumbnail-img {
  width: 36px;
  height: 36px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}

.no-image {
  color: #999;
  font-size: 12px;
}

.text-ellipsis {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}
</style>
