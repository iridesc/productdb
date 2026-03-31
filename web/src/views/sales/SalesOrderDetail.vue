<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
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

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref<SalesOrder | null>(null)
const id = route.params.id as string
const actionLoading = ref('')
const isEditing = ref(false)
const products = ref<any[]>([])
const showProductPicker = ref(false)
const tempItems = ref<any[]>([]) // 临时存储编辑时添加的商品

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

async function loadProducts() {
  try {
    showToast('加载商品列表...')
    const res: any = await getMaterials({ page_size: 100 })
    console.log('API Response:', res)
    products.value = res.items || []
    console.log('Loaded products:', products.value)
    if (products.value.length === 0) {
      showToast('暂无可用商品')
    } else {
      showToast(`加载成功，共${products.value.length}个商品`)
    }
  } catch (e) {
    console.error('Load products error:', e)
    showToast('加载商品列表失败')
    products.value = []
  }
}

// 编辑时初始化临时商品列表
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
  if (!detail.value?.customer_address) {
    showToast('客户地址不能为空')
    return
  }

  actionLoading.value = 'save'
  try {
    // 先保存基本信息
    await updateSalesOrder(id, {
      customer_name: detail.value.customer_name,
      customer_address: detail.value.customer_address,
      express_no: detail.value.express_no,
      remark: detail.value.remark
    })

    // 然后保存商品列表
    if (tempItems.value.length > 0) {
      await updateSalesOrderItems(id, tempItems.value.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.unit_price
      })))
    }

    showToast('保存成功')
    isEditing.value = false
    tempItems.value = []
    fetchDetail()
  } catch (e: any) {
    showToast(e.response?.data?.detail || e.message || '保存失败')
  } finally {
    actionLoading.value = ''
  }
}

async function handleAddProduct() {
  // 确保产品数据已加载
  if (products.value.length === 0) {
    showToast('正在加载商品列表...')
    await loadProducts()
  }
  showProductPicker.value = true
}

function addProduct(product: any) {
  if (!product || !product.id) {
    showToast('无法选择该商品')
    return
  }
  if (tempItems.value.find((i: any) => i.product_id === product.id)) {
    showToast('已添加该商品')
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
  showToast('添加成功')
  showProductPicker.value = false
}

// 编辑模式下删除商品
function removeTempProduct(index: number) {
  tempItems.value.splice(index, 1)
}

// 编辑模式下更新商品数量
function updateTempQuantity(index: number, quantity: number) {
  if (quantity > 0) {
    tempItems.value[index].quantity = quantity
    tempItems.value[index].amount = quantity * tempItems.value[index].unit_price
  }
}

// 计算临时总价
const tempTotalAmount = computed(() => {
  return tempItems.value.reduce((sum, item) => {
    return sum + (item.quantity * item.unit_price)
  }, 0)
})

// 发布订单
async function handlePublish() {
  await showConfirmDialog({ title: '确认发布', message: '发布后将开始发货流程' })
  actionLoading.value = 'publish'
  try {
    await publishSalesOrder(id)
    showToast('发布成功')
    fetchDetail()
  } catch (e: any) {
    const error = typeof e.response?.data?.detail === 'object' 
      ? e.response.data.detail.error + ': ' + e.response.data.detail.fields.join(', ')
      : (e.response?.data?.detail || e.message || '发布失败')
    showToast(error)
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

// 调试用：直接设置测试数据
function setTestData() {
  products.value = [
    { id: 1, name: '测试商品1', price: 100, is_active: true },
    { id: 2, name: '测试商品2', price: 200, is_active: true },
    { id: 3, name: '测试商品3', price: 300, is_active: true }
  ]
}
</script>

<template>
  <div class="sales-detail-page">
    <van-nav-bar title="订单详情" left-arrow @click-left="router.back()" />

    <div v-if="detail" class="detail-content">
      <!-- 订单信息 -->
      <div class="card">
        <div class="card-title-between">
          <span class="card-title">订单信息</span>
          <van-button 
            v-if="detail.status === 'draft' && !isEditing" 
            size="small" 
            type="primary" 
            @click="startEdit"
          >
            编辑
          </van-button>
        </div>
        
        <template v-if="isEditing">
          <van-field v-model="detail.customer_name" label="客户名称" placeholder="请输入（选填）" />
          <van-field v-model="detail.customer_address" label="客户地址" placeholder="请输入（必填）" required />
          <van-field v-model="detail.express_no" label="快递单号" placeholder="请输入（选填）" />
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
            <span class="label">客户</span>
            <span class="value">{{ detail.customer_name || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="label">客户地址</span>
            <span class="value">{{ detail.customer_address || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="label">快递单号</span>
            <span class="value">{{ detail.express_no || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="label">总金额</span>
            <span class="value price">¥{{ detail.total_amount }}</span>
          </div>
          <div v-if="detail.remark" class="info-row">
            <span class="label">备注</span>
            <span class="value">{{ detail.remark }}</span>
          </div>
        </template>
      </div>

      <!-- 商品列表 -->
      <div class="card">
        <div class="card-title-between">
          <span class="card-title">商品列表</span>
          <van-button
            v-if="detail.status === 'draft' && isEditing"
            size="small"
            type="primary"
            @click="handleAddProduct"
          >
            添加商品
          </van-button>
        </div>

        <!-- 编辑模式 -->
        <template v-if="isEditing">
          <div v-if="tempItems.length === 0" class="empty-tip">
            暂无商品，请添加商品
          </div>
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

        <!-- 非编辑模式 -->
        <template v-else>
          <div v-if="!detail.items || detail.items.length === 0" class="empty-tip">
            暂无商品{{ detail.status === 'draft' ? '，请在编辑模式下添加' : '' }}
          </div>
          <div v-else>
            <div
              v-for="item in detail.items"
              :key="item.id"
              class="product-item"
            >
              <div class="product-info">
                <div class="product-name">{{ item.product?.name || item.product_name }}</div>
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
        </template>
      </div>

      <!-- 编辑状态的操作按钮 -->
      <div v-if="isEditing" class="action-btns">
        <van-button type="default" block @click="cancelEdit">
          取消
        </van-button>
        <van-button 
          type="primary" 
          block 
          :loading="actionLoading === 'save'"
          @click="saveEdit"
          style="margin-top: 12px"
        >
          保存
        </van-button>
      </div>

      <!-- 正常状态的操作按钮 -->
      <div v-else class="action-btns">
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

    <van-popup v-model:show="showProductPicker" position="bottom" round>
      <van-picker
        title="选择商品"
        :columns="products.map(p => ({ text: p.name, value: p.id }))"
        @confirm="(selectedValue: any) => {
          if (selectedValue !== null) {
            const p = products.find(x => x.id === selectedValue)
            if (p) {
              addProduct(p)
            } else {
              showToast('无法选择该商品')
            }
          }
        }"
        @cancel="showProductPicker = false"
        :show-toolbar="true"
      />
    </van-popup>
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

.card-title-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-tip {
  text-align: center;
  padding: 24px;
  color: #999;
  font-size: 14px;
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

.total-row {
  display: flex;
  justify-content: space-between;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
  border-top: 1px solid #f5f5f5;
}

.total-price {
  color: #ff4d4f;
}
</style>