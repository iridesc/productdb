<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showDialog } from 'vant'
import {
  getProductionOrder,
  publishProductionOrder,
  startProductionOrder,
  completeProductionOrder,
  cancelProductionOrder,
  deleteProductionOrder,
} from '@/api/production'
import type { ProductionOrder } from '@/types/production'
import { showMessage, handleError } from '@/utils/request'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const detail = ref<ProductionOrder | null>(null)
const id = route.params.id as string
const actionLoading = ref('')

const isOperator = computed(() => userStore.isOperator())
const isWorker = computed(() => userStore.isWorker())

const statusMap: Record<string, string> = {
  draft: '草稿',
  pending: '待生产',
  in_production: '生产中',
  completed: '已完成',
  cancelled: '已取消'
}

async function fetchDetail() {
  loading.value = true
  try {
    detail.value = await getProductionOrder(id) as any
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    loading.value = false
  }
}

// 发布（仅运营/管理员，从草稿发布）
async function handlePublish() {
  await showConfirmDialog({ title: '确认发布', message: '发布后将检验物料库存并扣减，确定发布吗？' })
  actionLoading.value = 'publish'
  try {
    await publishProductionOrder(id)
    showMessage('发布成功，物料已扣减')
    fetchDetail()
  } catch (e: any) {
    // 物料库存不足时，展示带物料链接的详细信息
    const shortages = e?.response?.data?.detail?.shortages
    if (shortages && Array.isArray(shortages) && shortages.length > 0) {
      const lines = shortages.map((s: any) => {
        const name = s.material_name || s.material_code || '未知物料'
        const shortfall = s.required - s.current_stock
        return `<a href="/materials/${s.material_id}" target="_blank" style="color:#1989fa;text-decoration:none">${name}</a>：库存 <b>${s.current_stock}</b>，需要 <b>${s.required}</b>，缺少 <b style="color:#ff4d4f">${shortfall > 0 ? shortfall : 0}</b>`
      })
      showDialog({
        title: '物料库存不足',
        message: lines.join('<br/>'),
        allowHtml: true,
        confirmButtonText: '知道了',
      })
    } else {
      showMessage(handleError(e))
    }
  } finally {
    actionLoading.value = ''
  }
}

// 开工（仅工人/管理员）
async function handleStart() {
  await showConfirmDialog({ title: '确认开工', message: '确定要开始生产吗？' })
  actionLoading.value = 'start'
  try {
    await startProductionOrder(id)
    showMessage('已开工')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

// 报工完成（仅工人/管理员，成品入库）
async function handleComplete() {
  await showConfirmDialog({ title: '确认完成', message: '确定生产已完成吗？完成将自动入库。' })
  actionLoading.value = 'complete'
  try {
    await completeProductionOrder(id)
    showMessage('生产完成，成品已入库')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

// 取消（仅运营/管理员，仅待生产状态可取消）
async function handleCancel() {
  await showConfirmDialog({ title: '确认取消', message: '取消后将退回已扣物料库存，确定要取消吗？' })
  actionLoading.value = 'cancel'
  try {
    await cancelProductionOrder(id)
    showMessage('已取消，物料库存已退回')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

// 删除草稿
async function handleDelete() {
  await showConfirmDialog({ title: '确认删除', message: '确定要删除此草稿吗？此操作不可恢复。' })
  actionLoading.value = 'delete'
  try {
    await deleteProductionOrder(id)
    showMessage('已删除')
    router.back()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
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
    <van-nav-bar :title="`生产订单｜${detail?.order_no || ''}`" left-arrow @click-left="router.back()" />

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
          <span class="value status">{{ statusMap[detail.status] || detail.status }}</span>
        </div>
        <div class="info-row">
          <span class="label">产品</span>
          <span class="value">
            <a v-if="detail.product" :href="`/materials/${detail.product.id}`" target="_blank" class="link">{{ detail.product.name }}</a>
            <span v-else>{{ detail.product_name }}</span>
          </span>
        </div>
        <div class="info-row">
          <span class="label">生产数量</span>
          <span class="value">{{ detail.quantity }}</span>
        </div>
        <div class="info-row" v-if="detail.status === 'completed'">
          <span class="label">完成数量</span>
          <span class="value">{{ detail.completed_quantity }}</span>
        </div>
        <div class="info-row" v-if="detail.remark">
          <span class="label">备注</span>
          <span class="value">{{ detail.remark }}</span>
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
            <a :href="`/materials/${item.material_id}`" target="_blank" class="link">{{ item.material_name }}</a>
            <div class="material-quantity">需求: {{ item.quantity }}</div>
          </div>
        </div>
        <van-empty v-if="!detail.items || detail.items.length === 0" description="暂无物料" />
      </div>

      <!-- 操作按钮：按状态和角色显示 -->
      <div class="action-btns">
        <!-- 草稿：运营可编辑/删除/发布 -->
        <template v-if="detail.status === 'draft' && isOperator">
          <van-button type="primary" block :loading="actionLoading === 'publish'" @click="handlePublish">
            发布（校验库存并扣减）
          </van-button>
          <van-button
            type="danger"
            plain
            block
            :loading="actionLoading === 'delete'"
            @click="handleDelete"
            style="margin-top: 12px"
          >
            删除草稿
          </van-button>
        </template>

        <!-- 待生产：运营可取消，工人可开工 -->
        <template v-if="detail.status === 'pending'">
          <van-button v-if="isWorker" type="primary" block :loading="actionLoading === 'start'" @click="handleStart">
            开工
          </van-button>
          <van-button
            v-if="isOperator"
            type="danger"
            plain
            block
            :loading="actionLoading === 'cancel'"
            @click="handleCancel"
            :style="isWorker ? 'margin-top: 12px' : ''"
          >
            取消订单（退回物料）
          </van-button>
        </template>

        <!-- 生产中：工人可报工 -->
        <template v-if="detail.status === 'in_production' && isWorker">
          <van-button type="primary" block :loading="actionLoading === 'complete'" @click="handleComplete">
            报工完成（成品入库）
          </van-button>
        </template>

        <!-- 已完成/已取消：无操作 -->
        <template v-if="detail.status === 'completed' || detail.status === 'cancelled'">
          <van-button type="default" block disabled>
            {{ detail.status === 'completed' ? '订单已完成' : '订单已取消' }}
          </van-button>
        </template>

        <!-- 非运营/非工人提示 -->
        <van-empty
          v-if="!isOperator && !isWorker"
          description="暂无操作权限"
        />
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

.card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
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

.link {
  color: #1989fa;
  text-decoration: none;
  font-size: 14px;
}

.link:hover {
  text-decoration: underline;
}

.material-quantity {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.action-btns {
  padding: 16px;
}
</style>
