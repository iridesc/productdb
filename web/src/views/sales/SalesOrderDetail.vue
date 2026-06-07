<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { previewImage } from '@/utils/image'
import { showConfirmDialog } from 'vant'
import {
  getSalesOrder,
  updateSalesOrder,
  updateSalesOrderItems,
  publishSalesOrder,
  confirmSalesOrderItem,
  completeSalesOrder,
  cancelSalesOrder,
  deleteSalesOrder,
  getSalesOrderImages,
  uploadSalesOrderImage,
  deleteSalesOrderImage
} from '@/api/sales'
import { getMaterials } from '@/api/material'
import type { SalesOrder, SalesOrderImage, SalesOrderImageType } from '@/types/sales'
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
const orderImages = ref<SalesOrderImage[]>([])
const productShippingImages = computed(() => orderImages.value.filter(i => i.image_type === 'product_shipping'))
const logisticsImages = computed(() => orderImages.value.filter(i => i.image_type === 'logistics'))
const uploadingType = ref<SalesOrderImageType | ''>('')
const productImageInputRef = ref<HTMLInputElement | null>(null)
const logisticsImageInputRef = ref<HTMLInputElement | null>(null)
const productsCollapsed = ref(false)

// 四步工作流状态
const step1Done = computed(() => detail.value?.items?.every(i => i.is_confirmed) ?? false)
const step2Done = computed(() => productShippingImages.value.length > 0)
const step3Done = computed(() => logisticsImages.value.length > 0)
const step4Ready = computed(() => step1Done.value && step2Done.value && step3Done.value)

function toggleProducts() {
  productsCollapsed.value = !productsCollapsed.value
}

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
    await fetchOrderImages()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    loading.value = false
  }
}

async function fetchOrderImages() {
  if (!id) return
  try {
    orderImages.value = await getSalesOrderImages(id) as any
  } catch (e) {
    orderImages.value = []
  }
}

async function handleUploadImage(imageType: SalesOrderImageType, event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files.length) return

  const file = input.files[0]
  if (!file.type.startsWith('image/')) {
    showMessage('请选择图片文件')
    return
  }

  const sizeMB = (file.size / (1024 * 1024)).toFixed(2)
  if (file.size > 5 * 1024 * 1024) {
    await showConfirmDialog({
      title: '图片太大',
      message: `当前图片 ${sizeMB}MB，请选择小于 5MB 的图片`,
      showCancelButton: false,
      confirmButtonText: '知道了'
    })
    return
  }

  uploadingType.value = imageType
  try {
    await uploadSalesOrderImage(id, file, imageType)
    showMessage('上传成功')
    await fetchOrderImages()
  } catch (e: any) {
    await showConfirmDialog({
      title: '上传失败',
      message: e?.response?.data?.detail || '上传失败，请重试',
      showCancelButton: false
    })
  } finally {
    uploadingType.value = ''
    input.value = ''
  }
}

function triggerProductUpload() {
  productImageInputRef.value?.click()
}

function triggerLogisticsUpload() {
  logisticsImageInputRef.value?.click()
}

async function handleDeleteImage(imageId: string) {
  await showConfirmDialog({
    title: '确认删除',
    message: '确定要删除这张图片吗？'
  })
  try {
    await deleteSalesOrderImage(imageId)
    showMessage('删除成功')
    await fetchOrderImages()
  } catch (e) {
    // user cancelled
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
  await showConfirmDialog({ title: '确认发布', message: '发布后将锁定库存并进入待处理状态' })
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
    showMessage('已检查')
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
  await showConfirmDialog({ title: '确认取消', message: '确定要取消订单吗？已锁定的库存将自动退回' })
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

async function handleDelete() {
  await showConfirmDialog({
    title: '确认删除',
    message: '确定要删除这个草稿订单吗？此操作不可恢复。'
  })
  actionLoading.value = 'delete'
  try {
    await deleteSalesOrder(id)
    showMessage('删除成功')
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
  <div class="sales-detail-page">
    <van-nav-bar :title="`销售订单｜${detail?.order_no || ''}`" left-arrow @click-left="router.back()">
      <template #right>
        <div class="nav-actions">
          <van-icon v-if="detail?.status === 'draft' && !isEditing" name="edit" size="20" @click="startEdit" />
        </div>
      </template>
    </van-nav-bar>

    <div v-if="detail" class="detail-content">

      <!-- 工作流进度条 — 最顶部，仅 pending 状态 -->
      <div v-if="detail.status === 'pending'" class="workflow-steps">
        <div class="wf-step" :class="{ done: step1Done, active: !step1Done }">
          <div class="wf-step-num">1</div>
          <div class="wf-step-label">{{ step1Done ? '物料已检查' : '检查物料' }}</div>
        </div>
        <div class="wf-line" :class="{ done: step1Done }"></div>
        <div class="wf-step" :class="{ done: step2Done, active: step1Done && !step2Done, locked: !step1Done }">
          <div class="wf-step-num">2</div>
          <div class="wf-step-label">{{ step2Done ? '产品图已上传' : '产品发货图' }}</div>
        </div>
        <div class="wf-line" :class="{ done: step2Done }"></div>
        <div class="wf-step" :class="{ done: step3Done, active: step2Done && !step3Done, locked: !step2Done }">
          <div class="wf-step-num">3</div>
          <div class="wf-step-label">{{ step3Done ? '物流已确认' : '物流凭证图' }}</div>
        </div>
        <div class="wf-line" :class="{ done: step3Done }"></div>
        <div class="wf-step" :class="{ done: false, active: step4Ready, locked: !step4Ready }">
          <div class="wf-step-num">4</div>
          <div class="wf-step-label">完成订单</div>
        </div>
      </div>

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
            <div class="info-row total-amount">
              <span class="label">总金额</span>
              <span class="value price">¥{{ detail.total_amount }}</span>
            </div>
          </template>
        </div>

        <div class="card products-card">
          <div class="card-header clickable" @click="toggleProducts">
            <div class="card-title">
              <van-icon
                :name="productsCollapsed ? 'arrow' : 'arrow-down'"
                size="14"
                class="collapse-arrow"
                :class="{ rotated: !productsCollapsed }"
              />
              物料列表
            </div>
            <span v-if="detail.status === 'pending' && step1Done" class="step-done-tag">已全部检查</span>
            <van-button
              v-if="detail.status === 'draft' && isEditing"
              size="small"
              type="primary"
              @click.stop="handleAddProduct"
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
            <div v-show="!productsCollapsed">
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
                    @click="previewImage(item.product.thumbnail_url)"
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
                      class="action-btn-blue"
                      :loading="actionLoading === item.id"
                      @click="handleConfirmItem(item.id)"
                    >
                      <span class="pulse-dot"></span>
                      待检查
                    </van-button>
                    <van-button
                      v-else-if="item.is_confirmed"
                      size="small"
                      class="action-btn-done"
                      disabled
                    >
                      已检查
                    </van-button>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <!-- 产品发货图片 — 物料列表下方 -->
          <div v-if="(detail.status === 'pending' && step1Done) || (detail.status === 'completed' && productShippingImages.length > 0)" class="product-shipping-section">
            <div class="section-divider"></div>
            <div class="image-upload-label">
              <span>产品发货图片</span>
              <span v-if="detail.status === 'pending' && step1Done && !step2Done" class="pulse-dot" style="position:static;"></span>
              <span class="image-count">{{ productShippingImages.length > 0 ? '已上传' : '待上传' }}</span>
            </div>
            <div class="image-upload-row">
              <div
                v-for="img in productShippingImages"
                :key="img.id"
                class="uploaded-image-wrapper"
              >
                <img
                  :src="img.image_url"
                  class="uploaded-image"
                  @click="previewImage(img.image_url)"
                />
                <van-icon
                  v-if="detail.status === 'pending'"
                  name="close"
                  class="delete-image-icon"
                  @click="handleDeleteImage(img.id)"
                />
              </div>
              <div v-if="detail.status === 'pending'" class="upload-trigger" @click="triggerProductUpload">
                <van-icon name="plus" size="24" color="#999" />
                <span class="upload-text">上传</span>
              </div>
              <input
                ref="productImageInputRef"
                type="file"
                accept="image/*"
                style="display:none"
                @change="handleUploadImage('product_shipping', $event)"
              />
            </div>
          </div>
        </div>

        <!-- 物流单号 + 物流凭证图片 合并模块，仅 pending 状态 -->
        <div v-if="detail.status === 'pending'" class="card logistics-card" :class="{ 'full-width': true }">
          <div class="card-title">物流信息</div>
          <div class="info-row">
            <span class="label">物流单号</span>
            <span class="value">{{ detail.express_no || '-' }}</span>
          </div>

          <!-- 物流凭证图片 — step2（产品图上传）完成后解锁 -->
          <div v-if="step2Done" class="logistics-image-section">
            <div class="section-divider"></div>
            <div class="image-upload-label">
              <span>物流凭证图片</span>
              <span v-if="!step3Done && logisticsImages.length === 0" class="pulse-dot" style="position:static;"></span>
              <span class="image-count">{{ logisticsImages.length > 0 ? '已上传 · 物流已确认' : '待上传' }}</span>
            </div>
            <div class="image-upload-row">
              <div
                v-for="img in logisticsImages"
                :key="img.id"
                class="uploaded-image-wrapper"
              >
                <img
                  :src="img.image_url"
                  class="uploaded-image"
                  @click="previewImage(img.image_url)"
                />
                <van-icon
                  name="close"
                  class="delete-image-icon"
                  @click="handleDeleteImage(img.id)"
                />
              </div>
              <div class="upload-trigger" @click="triggerLogisticsUpload">
                <van-icon name="plus" size="24" color="#999" />
                <span class="upload-text">上传</span>
              </div>
              <input
                ref="logisticsImageInputRef"
                type="file"
                accept="image/*"
                style="display:none"
                @change="handleUploadImage('logistics', $event)"
              />
            </div>
          </div>
        </div>

        <div v-if="detail.remark && !isEditing" class="card remark-card full-width">
          <div class="card-title">备注</div>
          <div class="description">{{ detail.remark }}</div>
        </div>

        <!-- 物流信息 合并模块，仅 completed 状态 -->
        <div v-if="detail.status === 'completed' && (detail.express_no || logisticsImages.length > 0)" class="card logistics-card" :class="{ 'full-width': true }">
          <div class="card-title">物流信息</div>
          <div class="info-row">
            <span class="label">物流单号</span>
            <span class="value">{{ detail.express_no || '-' }}</span>
          </div>
          <div v-if="logisticsImages.length > 0" class="logistics-image-section">
            <div class="section-divider"></div>
            <div class="image-upload-label">
              <span>物流凭证图片</span>
            </div>
            <div class="image-upload-row">
              <img
                v-for="img in logisticsImages"
                :key="img.id"
                :src="img.image_url"
                class="uploaded-image"
                @click="previewImage(img.image_url)"
              />
            </div>
          </div>
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
          <div v-if="detail.status === 'draft'" class="action-btns">
            <van-button
              type="danger"
              plain
              block
              :loading="actionLoading === 'delete'"
              @click="handleDelete"
            >
              删除订单
            </van-button>
          </div>

          <template v-if="detail.status === 'pending'">

            <div class="action-btns">
              <van-button
                v-if="step4Ready"
                size="large"
                class="action-btn-blue action-block"
                round
                :loading="actionLoading === 'complete'"
                @click="handleComplete"
              >
                <span class="pulse-dot"></span>
                完成订单
              </van-button>
              <van-button
                v-else
                size="large"
                class="action-btn-disabled action-block"
                round
                disabled
              >
                {{ !step1Done ? '步骤① 请先检查所有物料' : !step2Done ? '步骤② 请上传产品发货图' : '步骤③ 请上传物流凭证图' }}
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

@keyframes pulse-dot-keyframes {
  0%, 100% { transform: scale(0.8); opacity: 0.6; }
  50% { transform: scale(1.4); opacity: 1; }
}

.pulse-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #1890ff;
  animation: pulse-dot-keyframes 1.2s ease-in-out infinite;
  margin-right: 6px;
  vertical-align: middle;
}

@keyframes collapse-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(180deg); }
}

.collapse-arrow {
  transition: transform 0.3s ease;
  margin-right: 4px;
}

.collapse-arrow.rotated {
  transform: rotate(180deg);
}

.clickable {
  cursor: pointer;
}

.step-done-tag {
  font-size: 12px;
  color: #07c160;
  font-weight: 500;
  background: #e8f8e8;
  padding: 2px 8px;
  border-radius: 4px;
}

.express-done-tag {
  font-size: 12px;
  color: #07c160;
  font-weight: 500;
  background: #e8f8e8;
  padding: 2px 8px;
  border-radius: 4px;
}

.workflow-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 16px;
  padding: 12px 12px;
  background: #fff;
  border-radius: 8px;
}

.wf-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.wf-step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  background: #eee;
  color: #999;
  transition: all 0.3s ease;
}

.wf-step.active .wf-step-num {
  background: #1890ff;
  color: #fff;
  box-shadow: 0 0 0 4px rgba(24,144,255,0.2);
}

.wf-step.done .wf-step-num {
  background: #07c160;
  color: #fff;
}

.wf-step.locked .wf-step-num {
  background: #f0f0f0;
  color: #ccc;
}

.wf-step-label {
  font-size: 11px;
  color: #999;
  white-space: nowrap;
}

.wf-step.active .wf-step-label {
  color: #1890ff;
  font-weight: 500;
}

.wf-step.done .wf-step-label {
  color: #07c160;
}

.wf-line {
  flex: 1;
  height: 2px;
  background: #eee;
  margin: 0 4px;
  margin-bottom: 22px;
  transition: background 0.3s ease;
}

.wf-line.done {
  background: #07c160;
}

.locked-card {
  opacity: 0.5;
  pointer-events: none;
}

.locked-text {
  color: #999;
  font-size: 13px;
  text-align: center;
  padding: 16px 0;
}

.section-divider {
  border-top: 1px solid #f0f0f0;
  margin: 12px 0;
}

.product-shipping-section,
.logistics-image-section {
  margin-top: 4px;
}

.product-shipping-section .image-upload-label,
.logistics-image-section .image-upload-label {
  margin-bottom: 10px;
}

.product-shipping-section .upload-trigger,
.logistics-image-section .upload-trigger {
  width: 72px;
  height: 72px;
}

.product-shipping-section .uploaded-image,
.logistics-image-section .uploaded-image {
  width: 72px;
  height: 72px;
}

.logistics-card {
  margin-bottom: 0;
}

.images-card {
  margin-bottom: 12px;
}

.image-upload-section {
  margin-bottom: 16px;
}

.image-upload-section:last-child {
  margin-bottom: 0;
}

.image-upload-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.image-count {
  font-size: 12px;
  font-weight: 400;
}

.image-upload-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: flex-start;
}

.uploaded-image-wrapper {
  position: relative;
  display: inline-flex;
}

.uploaded-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #eee;
  cursor: pointer;
}

.delete-image-icon {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #ff4d4f;
  color: #fff;
  border-radius: 50%;
  padding: 2px;
  font-size: 10px;
  cursor: pointer;
}

.upload-trigger {
  width: 80px;
  height: 80px;
  border: 1px dashed #ccc;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: #fafafa;
  transition: border-color 0.2s;
}

.upload-trigger:active {
  border-color: #1890ff;
}

.upload-text {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}
</style>
