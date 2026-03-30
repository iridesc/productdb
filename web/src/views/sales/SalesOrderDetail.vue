<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { 
  getSalesOrder, 
  publishSalesOrder, 
  confirmSalesOrderItem,
  confirmExpress,
  completeSalesOrder,
  cancelSalesOrder 
} from '@/api/sales'
import type { SalesOrder } from '@/types/sales'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref<SalesOrder | null>(null)
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
    detail.value = await getSalesOrder(id) as any
  } catch (e: any) {
    showToast(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// 发布订单
async function handlePublish() {
  await showConfirmDialog({ title: '确认发布', message: '发布后将开始发货流程' })
  actionLoading.value = 'publish'
  try {
    await publishSalesOrder(id)
    showToast('发布成功')
    fetchDetail()
  } catch (e: any) {
    showToast(e.message || '发布失败')
  } finally {
    actionLoading.value = ''
  }
}

// 确认商品
async function handleConfirmItem(itemId: string) {
  actionLoading.value = itemId
  try {
    await confirmSalesOrderItem(id, itemId)
    showToast('已确认，库存已扣减')
    fetchDetail()
  } catch (e: any) {
    showToast(e.message || '确认失败')
  } finally {
    actionLoading.value = ''
  }
}

// 确认快递单号
async function handleConfirmExpress() {
  actionLoading.value = 'express'
  try {
    await confirmExpress(id)
    showToast('快递单号已确认')
    fetchDetail()
  } catch (e: any) {
    showToast(e.message || '确认失败')
  } finally {
    actionLoading.value = ''
  }
}

// 完成订单
async function handleComplete() {
  await showConfirmDialog({ title: '确认完成', message: '确定订单已完成吗？' })
  actionLoading.value = 'complete'
  try {
    await completeSalesOrder(id)
    showToast('订单已完成')
    fetchDetail()
  } catch (e: any) {
    showToast(e.message || '操作失败')
  } finally {
    actionLoading.value = ''
  }
}

// 取消订单
async function handleCancel() {
  await showConfirmDialog({ title: '确认取消', message: '确定要取消订单吗？取消后不可撤回' })
  actionLoading.value = 'cancel'
  try {
    await cancelSalesOrder(id)
    showToast('订单已取消')
    fetchDetail()
  } catch (e: any) {
    showToast(e.message || '取消失败')
  } finally {
    actionLoading.value = ''
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="sales-detail-page">
    <van-nav-bar title="订单详情" left-arrow @click-left="router.back()" />

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
          <span class="label">客户</span>
          <span class="value">{{ detail.customer_name }}</span>
        </div>
        <div class="info-row">
          <span class="label">快递单号</span>
          <span class="value">{{ detail.express_no || '-' }}</span>
        </div>
        <div class="info-row">
          <span class="label">总金额</span>
          <span class="value price">¥{{ detail.total_amount }}</span>
        </div>
      </div>

      <!-- 商品列表 -->
      <div class="card">
        <div class="card-title">商品列表</div>
        <div 
          v-for="item in detail.items" 
          :key="item.id" 
          class="product-item"
        >
          <div class="product-info">
            <div class="product-name">{{ item.product_name }}</div>
            <div class="product-meta">
              {{ item.quantity }} × ¥{{ item.unit_price }} = ¥{{ item.amount }}
            </div>
          </div>
          <div class="product-action">
            <van-tag 
              :type="item.is_confirmed ? 'success' : 'warning'"
              size="large"
            >
              {{ item.is_confirmed ? '已确认' : '待确认' }}
            </van-tag>
            <van-button 
              v-if="detail.status === 'in_progress' && !item.is_confirmed"
              size="small" 
              type="primary"
              :loading="actionLoading === item.id"
              @click="handleConfirmItem(item.id)"
            >
              确认
            </van-button>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-btns">
        <!-- 草稿状态 -->
        <template v-if="detail.status === 'draft'">
          <van-button type="primary" block :loading="actionLoading === 'publish'" @click="handlePublish">
            发布订单
          </van-button>
        </template>
        
        <!-- 已发布状态 -->
        <template v-if="detail.status === 'published'">
          <van-button 
            v-if="!detail.items?.every(i => i.is_confirmed)"
            type="warning" 
            block 
            disabled
          >
            等待确认商品
          </van-button>
          <van-button 
            v-else
            type="primary" 
            block 
            :loading="actionLoading === 'express'"
            @click="handleConfirmExpress"
          >
            确认快递单号
          </van-button>
        </template>

        <!-- 进行中状态 -->
        <template v-if="detail.status === 'in_progress'">
          <van-button 
            type="primary" 
            block 
            :loading="actionLoading === 'complete'"
            @click="handleComplete"
          >
            完成订单
          </van-button>
        </template>

        <!-- 已发布/进行中 可取消 -->
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
.sales-detail-page {
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

.value.price {
  color: #ff4d4f;
  font-weight: 600;
}

.product-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
}

.product-item:last-child {
  border-bottom: none;
}

.product-info {
  flex: 1;
}

.product-name {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.product-meta {
  font-size: 12px;
  color: #999;
}

.product-action {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btns {
  padding: 16px;
}
</style>