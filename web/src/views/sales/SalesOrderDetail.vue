<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
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
import ProductSelector from '@/components/ProductSelector.vue'
import type { SalesOrder, SalesOrderImage, SalesOrderImageType } from '@/types/sales'
import { showMessage, handleError } from '@/utils/request'
import { formatNumber } from '@/utils/number'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const hasPermission = computed(() => userStore.hasPermission('can_manage_sales'))
const isAdmin = computed(() => userStore.userInfo?.is_superuser === true)
const loading = ref(false)
const detail = ref<SalesOrder | null>(null)
const id = route.params.id as string
const actionLoading = ref('')
const isEditing = ref(false)
const showProductPicker = ref(false)
const tempItems = ref<any[]>([])
const orderImages = ref<SalesOrderImage[]>([])
const productShippingImages = computed(() => orderImages.value.filter(i => i.image_type === 'product_shipping'))
const logisticsImages = computed(() => orderImages.value.filter(i => i.image_type === 'logistics'))
const uploadingType = ref<SalesOrderImageType | ''>('')

// 相机拍照
const showCamera = ref(false)
const cameraImageType = ref<SalesOrderImageType | ''>('')
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let cameraStream: MediaStream | null = null

// 四步工作流状态
const step1Done = computed(() => detail.value?.items?.every(i => i.is_confirmed) ?? false)
const step2Done = computed(() => productShippingImages.value.length > 0)
const step3Done = computed(() => logisticsImages.value.length > 0)
const step4Ready = computed(() => step1Done.value && step2Done.value && step3Done.value)

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
      data.customer_info = data.customer_info || ''
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

async function openCamera(imageType: SalesOrderImageType) {
  cameraImageType.value = imageType
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } }
    })
    showCamera.value = true
    await nextTick()
    if (videoRef.value) {
      videoRef.value.srcObject = cameraStream
    }
  } catch (e) {
    showMessage('无法打开相机，请检查权限设置')
  }
}

function closeCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop())
    cameraStream = null
  }
  showCamera.value = false
  cameraImageType.value = ''
}

async function capturePhoto() {
  const video = videoRef.value
  const canvas = canvasRef.value
  if (!video || !canvas) return

  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(video, 0, 0)

  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((b) => {
      if (b) resolve(b)
      else reject(new Error('capture failed'))
    }, 'image/jpeg', 0.9)
  })

  const file = new File([blob], `camera_${Date.now()}.jpg`, { type: 'image/jpeg' })

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

  const imageType = cameraImageType.value
  uploadingType.value = imageType
  closeCamera()

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
  }
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


function initTempItems() {
  if (detail.value?.items) {
    tempItems.value = detail.value.items.map((item: any) => ({
      ...item,
      thumbnail_url: item.product?.thumbnail_url || item.thumbnail_url || ''
    }))
  } else {
    tempItems.value = []
  }
}

function startEdit() {
  isEditing.value = true
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
      customer_info: detail.value.customer_info,
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

function handleAddProduct() {
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
    is_confirmed: false,
    thumbnail_url: product.thumbnail_url || ''
  })
  showMessage('添加成功')
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

// 取消订单（仅管理员，两步确认）
async function handleCancel() {
  // 第一步：确认是否取消
  try {
    await showConfirmDialog({
      title: '取消销售订单',
      message: '确定要取消此订单吗？',
      confirmButtonText: '继续取消',
      cancelButtonText: '取消操作',
    })
  } catch {
    return // 用户点击「取消操作」，关闭弹窗
  }

  // 第二步：选择是否退回库存
  let returnInventory = true
  try {
    await showConfirmDialog({
      title: '取消销售订单',
      message: '已锁定物料库存是否退回？',
      confirmButtonText: '退回库存并取消',
      cancelButtonText: '不退回直接取消',
    })
  } catch {
    returnInventory = false
  }

  actionLoading.value = 'cancel'
  try {
    await cancelSalesOrder(id, returnInventory)
    showMessage(returnInventory ? '已取消，物料库存已退回' : '已取消，物料库存未退回')
    fetchDetail()
  } catch (e) {
    showMessage(handleError(e))
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
    <template v-if="hasPermission">
    <van-nav-bar :title="`销售订单｜${detail?.order_no || ''}`" left-arrow @click-left="router.push('/sales-orders')">
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
          <div class="wf-step-label">{{ step2Done ? '物料凭证图已上传' : '物料凭证图片' }}</div>
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
              <span class="value price">¥{{ formatNumber(detail.total_amount) }}</span>
            </div>
          </template>
        </div>

        <div class="card products-card">
          <div class="card-title">
            <span v-if="detail.status === 'pending' && !step1Done" class="pulse-dot"></span>
            物料列表
            <span v-if="detail.status === 'pending' && step1Done" class="step-done-tag">已全部检查</span>
          </div>
          <van-button
            v-if="detail.status === 'draft' && isEditing"
            size="small"
            type="primary"
            @click.stop="handleAddProduct"
            style="margin-bottom: 12px"
          >
            添加物料
          </van-button>

          <template v-if="isEditing">
            <div v-if="tempItems.length === 0" class="empty-text">暂无物料，请添加物料</div>
            <div v-else>
              <div
                v-for="(item, index) in tempItems"
                :key="index"
                class="product-item"
              >
                <img
                  v-if="item.thumbnail_url"
                  class="product-thumb"
                  :src="item.thumbnail_url"
                  :alt="item.product_name"
                />
                <div v-else class="product-thumb product-thumb-placeholder">
                  <van-icon name="photo-o" size="20" />
                </div>
                <div class="item-body">
                  <div class="item-header">
                    <span class="item-code">{{ item.product?.code || '—' }}</span>
                    <span class="item-stock">¥{{ formatNumber(item.unit_price) }} / 件</span>
                  </div>
                  <div class="item-name">{{ item.product_name }}</div>
                </div>
                <div class="item-action edit-actions">
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
                <span class="total-price">¥{{ formatNumber(tempTotalAmount) }}</span>
              </div>
            </div>
          </template>

          <template v-else>
            <div>
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
                  <div class="item-body">
                    <div class="item-header">
                      <span class="item-code">{{ item.product?.code || '—' }}</span>
                      <span v-if="detail.status === 'draft'" class="item-stock">可用库存: <b>{{ formatNumber(item.product?.current_stock ?? 0) }}</b></span>
                      <span class="item-qty-tag">数量：{{ Math.round(Number(item.quantity)) }}</span>
                   </div>
                   <div class="item-name">{{ item.product?.name || item.product_name }}</div>
                 </div>
                  <div class="item-action">
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
                    <span v-else-if="item.is_confirmed" class="check-done-tag">已检查</span>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <!-- 物料凭证图片 — 物料列表下方 -->
          <div v-if="(detail.status === 'pending' && step1Done) || (detail.status === 'completed' && productShippingImages.length > 0)" class="product-shipping-section">
            <div class="section-divider"></div>
            <div class="image-upload-label">
              <span><span v-if="detail.status === 'pending' && step1Done && !step2Done" class="pulse-dot"></span>物料凭证图片</span>
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
              <div v-if="detail.status === 'pending'" class="upload-trigger" @click="openCamera('product_shipping')">
                <van-icon name="plus" size="24" color="#999" />
                <span class="upload-text"><span v-if="!step2Done" class="pulse-dot"></span>拍照</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 物流单号 + 物流凭证图片 合并模块，仅 pending 状态 -->
        <div v-if="detail.status === 'pending'" class="card logistics-card" :class="{ 'full-width': true }">
          <div class="card-title">
            <span v-if="step2Done && !step3Done" class="pulse-dot"></span>
            物流信息
          </div>
          <div class="express-no-text">{{ detail.express_no || '-' }}</div>

          <!-- 物流凭证图片 — step2（物料凭证图上传）完成后解锁 -->
          <div v-if="step2Done" class="logistics-image-section">
            <div class="section-divider"></div>
            <div class="image-upload-label">
              <span><span v-if="!step3Done && logisticsImages.length === 0" class="pulse-dot"></span>物流凭证图片</span>
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
              <div class="upload-trigger" @click="openCamera('logistics')">
                <van-icon name="plus" size="24" color="#999" />
                <span class="upload-text"><span v-if="!step3Done" class="pulse-dot"></span>拍照</span>
              </div>
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
          <div class="express-no-text">{{ detail.express_no || '-' }}</div>
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
                {{ !step1Done ? '步骤① 请先检查所有物料' : !step2Done ? '步骤② 请上传物料凭证图片' : '步骤③ 请上传物流图片' }}
              </van-button>
              <!-- 仅管理员可取消 -->
              <van-button
                v-if="isAdmin"
                type="danger"
                plain
                block
                :loading="actionLoading === 'cancel'"
                @click="handleCancel"
                style="margin-top: 12px"
              >
                取消订单
              </van-button>
            </div>
          </template>
        </template>
      </div>
    </div>

    <!-- 相机拍照取景器 -->
    <van-popup
      v-model:show="showCamera"
      position="bottom"
      round
      :style="{ width: '100%', height: '100%', background: '#000' }"
      @click-overlay="closeCamera"
    >
      <div class="camera-viewfinder">
        <video ref="videoRef" autoplay playsinline class="camera-video"></video>
        <canvas ref="canvasRef" style="display:none"></canvas>
        <div class="camera-controls">
          <van-button round plain class="camera-cancel-btn" @click="closeCamera">取消</van-button>
          <div class="camera-capture-btn" @click="capturePhoto">
            <div class="capture-ring"></div>
          </div>
          <div style="width: 64px"></div>
        </div>
      </div>
    </van-popup>

    <!-- 商品选择器（带搜索） -->
    <ProductSelector
      v-model="showProductPicker"
      @select="addProduct"
    />
    </template>
    <van-empty v-else description="暂无权限，请联系管理员" />
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
  border-bottom: 1px solid #ebebeb;
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

.item-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-code {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  font-family: monospace;
}

.item-stock {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.item-stock b {
  color: #333;
}


.item-qty-tag {
  display: inline-flex;
  align-items: center;
  height: 100%;
  margin-left: auto;
  font-size: 14px;
  font-weight: 600;
  color: #ff4d4f;
}

.item-name {
  font-size: 13px;
  color: #666;
}

.item-action {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.item-action.edit-actions {
  gap: 8px;
}

.remove-btn {
  color: #ff4d4f;
  cursor: pointer;
  font-size: 18px;
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

.action-btn-blue {
  background-color: #1890ff !important;
  border-color: #1890ff !important;
  color: #fff !important;
  font-weight: 500;
}

.check-done-tag {
  font-size: 12px;
  color: #07c160;
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

.express-no-text {
  font-size: 16px;
  color: #333;
  font-weight: 500;
  padding: 4px 0;
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

/* 相机取景器 */
.camera-viewfinder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  flex: 1;
}

.camera-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px 48px;
  background: linear-gradient(transparent, rgba(0,0,0,0.6));
}

.camera-cancel-btn {
  color: #fff !important;
  border-color: rgba(255,255,255,0.5) !important;
  width: 64px;
}

.camera-capture-btn {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 4px solid #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.15s;
}

.camera-capture-btn:active {
  transform: scale(0.9);
}

.capture-ring {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #fff;
}
</style>
