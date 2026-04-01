<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog } from 'vant'
import {
  getSalesOrder,
  updateSalesOrder,
  updateSalesOrderItems,
  publishSalesOrder,
  confirmSalesOrderItem,
  confirmExpress,
  completeSalesOrder,
  cancelSalesOrder
} from '@/api/sales'
import { getMaterials } from '@/api/material'
import type { SalesOrder } from '@/types/sales'
import { showMessage, handleError } from '@/utils/request'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref<SalesOrder | null>(null)
const id = route.params.id as string
const actionLoading = ref('')
const isEditing = ref(false)
const products = ref<any[]>([])
const showProductPicker = ref(false)
const tempItems = ref<any[]>([])
const materialSearchText = ref('')

const statusMap: Record<string, string> = {
  draft: '草稿',
  pending: '待处理',
  completed: '已完成',
  cancelled: '已取消'
}

async function fetchDetail() {
  loading.value = true
  try {
    const data = await getSalesOrder(id) as any
    if (data) {
      data.customer_info = data.customer_name || data.customer_address || ''
    }
    detail.value = data
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    loading.value = false
  }
}

async function loadProducts() {
  try {
    const res: any = await getMaterials({ page_size: 100 })
    products.value = res.items || []
  } catch (e) {
    console.error('Load products error:', e)
    const errorMessage = handleError(e)
    showMessage(errorMessage)
    products.value = []
  }
}

function initTempItems() {
  if (detail.value?.items) {
    tempItems.value = [...detail.value.items]
  } else {
    tempItems.value = []
  }
}

function startEdit() {
  isEditing.value = true
  loadProducts()
  initTempItems()
}

function cancelEdit() {
  isEditing.value = false
  tempItems.value = []
}

async function saveEdit() {
  if (!detail.value?.customer_info) {
    showMessage('客户信息不能为空')
    return
  }

  actionLoading.value = 'save'
  try {
    await updateSalesOrder(id, {
      customer_name: detail.value.customer_info,
      customer_address: detail.value.customer_info,
      express_no: detail.value.express_no,
      remark: detail.value.remark
    })

    if (tempItems.value.length > 0) {
      await updateSalesOrderItems(id, tempItems.value.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.unit_price
      })))
    }

    showMessage('保存成功')
    isEditing.value = false
    tempItems.value = []
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

async function handleAddProduct() {
  if (products.value.length === 0) {
    await loadProducts()
  }
  showProductPicker.value = true
}

function addProduct(product: any) {
  if (!product || !product.id) {
    showMessage('无法选择该商品')
    return
  }
  if (tempItems.value.find((i: any) => i.product_id === product.id)) {
    showMessage('已添加该商品')
    return
  }
  tempItems.value.push({
    product_id: product.id,
    product_name: product.name,
    quantity: 1,
    unit_price: product.price || 0,
    amount: product.price || 0,
    is_confirmed: false
  })
  showMessage('添加成功')
  showProductPicker.value = false
}

function removeTempProduct(index: number) {
  tempItems.value.splice(index, 1)
}

function updateTempQuantity(index: number, quantity: number) {
  if (quantity > 0) {
    tempItems.value[index].quantity = quantity
    tempItems.value[index].amount = quantity * tempItems.value[index].unit_price
  }
}

const tempTotalAmount = computed(() => {
  return tempItems.value.reduce((sum, item) => {
    return sum + (item.quantity * item.unit_price)
  }, 0)
})

const filteredProducts = computed(() => {
  if (!materialSearchText.value) return products.value
  const keyword = materialSearchText.value.toLowerCase()
  return products.value.filter((p: any) =>
    p.name?.toLowerCase().includes(keyword) ||
    p.code?.toLowerCase().includes(keyword)
  )
})

function onSearchMaterials() {}

async function handlePublish() {
  await showConfirmDialog({ title: '确认发布', message: '发布后将进入待处理状态，发货人员可进行物料分配' })
  actionLoading.value = 'publish'
  try {
    await publishSalesOrder(id)
    showMessage('发布成功')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

async function handleConfirmItem(itemId: string) {
  actionLoading.value = itemId
  try {
    await confirmSalesOrderItem(id, itemId)
    showMessage('已分配，库存已扣减')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

async function handleConfirmExpress() {
  actionLoading.value = 'express'
  try {
    await confirmExpress(id)
    showMessage('物流单号已确认')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

async function handleComplete() {
  await showConfirmDialog({ title: '确认完成', message: '确定订单已完成吗？' })
  actionLoading.value = 'complete'
  try {
    await completeSalesOrder(id)
    showMessage('订单已完成')
    fetchDetail()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    actionLoading.value = ''
  }
}

async function handleCancel() {
  await showConfirmDialog({ title: '确认取消', message: '确定要取消订单吗？已分配的库存将自动退回' })
  actionLoading.value = 'cancel'
  try {
    await cancelSalesOrder(id)
    showMessage('订单已取消')
    fetchDetail()
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
  <div class="sales-detail-page">
    <van-nav-bar :title="`销售订单｜${detail?.order_no || ''}`" left-arrow @click-left="router.back()">
      <template #right>
        <div class="nav-actions">
          <van-icon v-if="detail?.status === 'draft' && !isEditing" name="edit" size="20" @click="startEdit" />
        </div>
      </template>
    </van-nav-bar>

    <div v-if="detail" class="detail-content">
      <div class="detail-grid">
        <div class="card order-info-card">
          <div class="card-title">订单信息</div>

          <template v-if="isEditing">
            <van-field v-model="detail.customer_info" label="客户信息" placeholder="请输入客户名称、地址、电话等" type="textarea" rows="3" required />
            <van-field v-model="detail.express_no" label="物流单号" placeholder="请输入物流单号" />
            <van-field v-model="detail.remark" label="备注" placeholder="请输入（选填）" type="textarea" rows="2" />
          </template>

          <template v-else>
            <div class="info-row">
              <span class="label">订单号</span>
              <span class="value">{{ detail.order_no }}</span>
            </div>
            <div class="info-row">
              <span class="label">状态</span>
              <span class="value status">{{ statusMap[detail.status] }}</span>
            </div>
            <div class="info-row">
              <span class="label">客户信息</span>
              <span class="value">{{ detail.customer_info || '-' }}</span>
            </div>
            <div class="info-row">
              <span class="label">物流单号</span>
              <span class="value express-row">
                <span>{{ detail.express_no || '-' }}</span>
                <van-button
                  v-if="detail.status === 'pending' && !detail.express_confirmed"
                  size="small"
                  :class="{ 'action-btn-shake': detail.items?.every(i => i.is_confirmed), 'action-btn-blue': true, 'action-btn-disabled': !detail.items?.every(i => i.is_confirmed) }"
                  :disabled="!detail.items?.every(i => i.is_confirmed)"
                  :loading="actionLoading === 'express'"
                  @click="handleConfirmExpress"
                >
                  待确认
                </van-button>
                <van-button
                  v-if="detail.status === 'pending' && detail.express_confirmed"
                  size="small"
                  class="action-btn-done"
                  disabled
                >
                  已确认
                </van-button>
              </span>
            </div>
            <div class="info-row total-amount">
              <span class="label">总金额</span>
              <span class="value price">¥{{ detail.total_amount }}</span>
            </div>
          </template>
        </div>

        <div class="card products-card">
          <div class="card-header">
            <div class="card-title">物料列表</div>
            <van-button
              v-if="detail.status === 'draft' && isEditing"
              size="small"
              type="primary"
              @click="handleAddProduct"
            >
              添加物料
            </van-button>
          </div>

          <template v-if="isEditing">
            <div v-if="tempItems.length === 0" class="empty-text">暂无物料，请添加物料</div>
            <div v-else>
              <div
                v-for="(item, index) in tempItems"
                :key="index"
                class="product-item"
              >
                <div class="product-info">
                  <div class="product-name">{{ item.product_name }}</div>
                  <div class="product-meta">
                    ¥{{ item.unit_price }}
                  </div>
                </div>
                <div class="product-actions">
                  <van-stepper
                    v-model="item.quantity"
                    :min="1"
                    @change="(val: number) => updateTempQuantity(index, val)"
                  />
                  <van-icon name="cross" class="remove-btn" @click="removeTempProduct(index)" />
                </div>
              </div>
              <div class="total-row">
                <span>合计</span>
                <span class="total-price">¥{{ tempTotalAmount }}</span>
              </div>
            </div>
          </template>

          <template v-else>
            <div v-if="!detail.items || detail.items.length === 0" class="empty-text">
              暂无物料{{ detail.status === 'draft' ? '，请在编辑模式下添加' : '' }}
            </div>
            <div v-else>
              <div
                v-for="item in detail.items"
                :key="item.id"
                class="product-item"
              >
                <img
                  v-if="item.product?.thumbnail_url"
                  class="product-thumb"
                  :src="item.product.thumbnail_url"
                  :alt="item.product?.name || item.product_name"
                />
                <div v-else class="product-thumb product-thumb-placeholder">
                  <van-icon name="photo-o" size="20" />
                </div>
                <div class="product-info">
                  <div class="product-name">{{ item.product?.name || item.product_name }}</div>
                  <div class="product-meta">
                    {{ item.quantity }} × ¥{{ item.unit_price }} = ¥{{ item.amount }}
                  </div>
                </div>
                <div class="product-action">
                  <van-button
                    v-if="detail.status === 'pending' && !item.is_confirmed"
                    size="small"
                    class="action-btn-shake action-btn-blue"
                    :loading="actionLoading === item.id"
                    @click="handleConfirmItem(item.id)"
                  >
                    待分配
                  </van-button>
                  <van-button
                    v-else-if="item.is_confirmed"
                    size="small"
                    class="action-btn-done"
                    disabled
                  >
                    已分配
                  </van-button>
                </div>
              </div>
            </div>
          </template>
        </div>

        <div v-if="detail.remark && !isEditing" class="card remark-card full-width">
          <div class="card-title">备注</div>
          <div class="description">{{ detail.remark }}</div>
        </div>
      </div>

      <div class="actions-section">
        <template v-if="isEditing">
          <div class="edit-btns">
            <van-button type="default" block @click="cancelEdit">取消</van-button>
            <van-button type="primary" block :loading="actionLoading === 'save'" @click="saveEdit">保存</van-button>
          </div>
        </template>

        <template v-else>
          <div v-if="detail.status === 'draft'" class="action-btns">
            <van-button type="primary" block :loading="actionLoading === 'publish'" @click="handlePublish">
              发布订单
            </van-button>
          </div>

          <template v-if="detail.status === 'pending'">
            <div class="action-btns">
              <van-button
                v-if="detail.items?.every(i => i.is_confirmed) && detail.express_confirmed"
                size="large"
                class="action-btn-shake action-btn-blue action-block"
                round
                :loading="actionLoading === 'complete'"
                @click="handleComplete"
              >
                完成订单
              </van-button>
              <van-button
                v-if="!detail.items?.every(i => i.is_confirmed) || !detail.express_confirmed"
                size="large"
                class="action-btn-disabled action-block"
                round
                disabled
              >
                {{ !detail.items?.every(i => i.is_confirmed) ? '等待分配所有物料' : '等待确认物流' }}
              </van-button>
            </div>
            <div class="action-btns">
              <van-button
                type="danger"
                plain
                block
                :loading="actionLoading === 'cancel'"
                @click="handleCancel"
              >
                取消订单
              </van-button>
            </div>
          </template>
        </template>
      </div>
    </div>

    <van-popup v-model:show="showProductPicker" position="bottom" round style="height: 70%">
      <div class="material-picker">
        <van-search v-model="materialSearchText" placeholder="搜索物料名称或编码" @search="onSearchMaterials" @clear="onSearchMaterials" />
        <div class="material-list">
          <van-cell
            v-for="item in filteredProducts"
            :key="item.id"
            :title="item.name"
            :label="`${item.code} | ¥${item.price || 0} | 库存: ${item.current_stock || 0}`"
            clickable
            @click="addProduct(item)"
          >
            <template #right-icon>
              <van-icon name="plus" size="18" color="#1890ff" />
            </template>
          </van-cell>
          <div v-if="filteredProducts.length === 0" class="empty-text">无匹配物料</div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.sales-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.nav-actions {
  display: flex;
  align-items: center;
}

.nav-actions .van-icon {
  cursor: pointer;
}

.detail-content {
  padding: 16px;
  max-width: 1400px;
  margin: 0 auto;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

@media (min-width: 768px) {
  .detail-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .full-width {
    grid-column: 1 / -1;
  }
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-header .card-title {
  margin-bottom: 0;
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
  display: flex;
  align-items: center;
  gap: 8px;
}

.value.status {
  color: #1989fa;
}

.value.price {
  color: #ff4d4f;
  font-weight: 600;
}

.express-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.total-amount {
  background: #f5f5f5;
  margin: 0 -16px;
  padding: 10px 16px;
  border-radius: 0 0 8px 8px;
}

.total-amount .label,
.total-amount .value {
  font-weight: 600;
}

.empty-text {
  text-align: center;
  padding: 24px;
  color: #999;
  font-size: 14px;
}

.product-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
}

.product-item:last-child {
  border-bottom: none;
}

.product-thumb {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
  background: #f5f5f5;
}

.product-thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ccc;
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

.product-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.remove-btn {
  color: #ff4d4f;
  cursor: pointer;
}

.description {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

.actions-section {
  margin-top: 12px;
}

.edit-btns {
  display: flex;
  gap: 12px;
  padding: 16px 0;
}

.edit-btns .van-button {
  flex: 1;
}

.action-btns {
  padding: 8px 0;
}

.action-block {
  width: 100%;
}

.total-row {
  display: flex;
  justify-content: space-between;
  padding: 16px 0;
  font-size: 16px;
  font-weight: 600;
  border-top: 1px solid #f5f5f5;
}

.total-price {
  color: #ff4d4f;
}

.material-picker {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.material-list {
  flex: 1;
  overflow-y: auto;
}

.action-btn-blue {
  background-color: #1890ff !important;
  border-color: #1890ff !important;
  color: #fff !important;
  font-weight: 500;
}

.action-btn-done {
  background-color: #07c160 !important;
  border-color: #07c160 !important;
  color: #fff !important;
  font-weight: 500;
}

.action-btn-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  15%, 45%, 75% { transform: translateX(-3px); }
  30%, 60%, 90% { transform: translateX(3px); }
}

.action-btn-shake {
  animation: shake 2s ease-in-out infinite;
}
</style>
