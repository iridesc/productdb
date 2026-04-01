<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { 
  getProductionOrder, 
  publishProductionOrder,
  distributeProductionItem,
  completeProductionOrder,
  cancelProductionOrder
} from '@/api/production'
import type { ProductionOrder } from '@/types/production'
import { handleError } from '@/utils/request'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref<ProductionOrder | null>(null)
const id = route.params.id as string
const actionLoading = ref('')

const statusMap: Record<string, string> = {
  draft: '草稿',
  published: '已发布',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消'
}

async function fetchDetail() {
  loading.value = true
  try {
    detail.value = await getProductionOrder(id) as any
  } catch (e) {
    const errorMessage = handleError(e)
    showToast(errorMessage)
  } finally {
    loading.value = false
  }
}

// 发布
async function handlePublish() {
  await showConfirmDialog({ title: '确认发布', message: '发布后将开始生产流程' })
  actionLoading.value = 'publish'
  try {
    await publishProductionOrder(id)
    showToast('发布成功')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showToast(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

// 分配物料
async function handleDistribute(itemId: string) {
  actionLoading.value = itemId
  try {
    await distributeProductionItem(id, itemId)
    showToast('库存已分配')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showToast(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

// 完成
async function handleComplete() {
  await showConfirmDialog({ title: '确认完成', message: '确定生产已完成吗？' })
  actionLoading.value = 'complete'
  try {
    await completeProductionOrder(id)
    showToast('生产完成，成品已入库')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showToast(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

// 取消
async function handleCancel() {
  await showConfirmDialog({ title: '确认取消', message: '确定要取消吗？' })
  actionLoading.value = 'cancel'
  try {
    await cancelProductionOrder(id)
    showToast('已取消')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showToast(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="production-detail-page">
    <van-nav-bar title="生产订单详情" left-arrow @click-left="router.back()" />

    <div v-if="detail" class="detail-content">
      <!-- 订单信息 -->
      <div class="card">
        <div class="card-title">订单信息</div>
        <div class="info-row">
          <span class="label">订单号</span>
          <span class="value">{{ detail.order_no }}</span>
        </div>
        <div class="info-row">
          <span class="label">状态</span>
          <span class="value status">{{ statusMap[detail.status] }}</span>
        </div>
        <div class="info-row">
          <span class="label">产品</span>
          <span class="value">{{ detail.product_name }}</span>
        </div>
        <div class="info-row">
          <span class="label">生产数量</span>
          <span class="value">{{ detail.quantity }}</span>
        </div>
      </div>

      <!-- BOM物料 -->
      <div class="card">
        <div class="card-title">物料需求</div>
        <div 
          v-for="item in detail.items" 
          :key="item.id" 
          class="material-item"
        >
          <div class="material-info">
            <div class="material-name">{{ item.material_name }}</div>
            <div class="material-quantity">需求: {{ item.quantity }}</div>
          </div>
          <div class="material-action">
            <van-tag :type="item.is_distributed ? 'success' : 'warning'" size="large">
              {{ item.is_distributed ? '已分配' : '待分配' }}
            </van-tag>
            <van-button 
              v-if="detail.status === 'in_progress' && !item.is_distributed"
              size="small" 
              type="primary"
              :loading="actionLoading === item.id"
              @click="handleDistribute(item.id)"
            >
              分配
            </van-button>
          </div>
        </div>
      </div>

      <!-- 操作 -->
      <div class="action-btns">
        <template v-if="detail.status === 'draft'">
          <van-button type="primary" block :loading="actionLoading === 'publish'" @click="handlePublish">
            发布订单
          </van-button>
        </template>

        <template v-if="detail.status === 'published'">
          <van-button type="warning" block disabled>
            等待生产人员分配物料
          </van-button>
        </template>

        <template v-if="detail.status === 'in_progress'">
          <van-button 
            v-if="!detail.items?.every(i => i.is_distributed)"
            type="warning" 
            block 
            disabled
          >
            等待分配所有物料
          </van-button>
          <van-button 
            v-else
            type="primary" 
            block 
            :loading="actionLoading === 'complete'"
            @click="handleComplete"
          >
            完成生产
          </van-button>
        </template>

        <template v-if="['published', 'in_progress'].includes(detail.status)">
          <van-button 
            type="danger" 
            plain 
            block 
            :loading="actionLoading === 'cancel'"
            @click="handleCancel"
            style="margin-top: 12px"
          >
            取消订单
          </van-button>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.production-detail-page {
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

.label {
  color: #999;
  font-size: 14px;
}

.value {
  color: #333;
  font-size: 14px;
}

.value.status {
  color: #1989fa;
}

.material-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
}

.material-item:last-child {
  border-bottom: none;
}

.material-name {
  font-size: 14px;
  color: #333;
}

.material-quantity {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.material-action {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btns {
  padding: 16px;
}
</style>