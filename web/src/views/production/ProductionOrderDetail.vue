<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showDialog } from 'vant'
import {
  getProductionOrder,
  updateProductionOrder,
  publishProductionOrder,
  startProductionOrder,
  completeProductionOrder,
  cancelProductionOrder,
  deleteProductionOrder,
  distributeProductionItem,
  setProductionYield,
  uploadProductionOrderImage,
  deleteProductionOrderImage,
} from '@/api/production'
import type { ProductionOrder, ProductionOrderUpdate } from '@/types/production'
import { showMessage, handleError } from '@/utils/request'
import { previewImage } from '@/utils/image'
import { useUserStore } from '@/store/user'
import ProductSelector from '@/components/ProductSelector.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const detail = ref<ProductionOrder | null>(null)
const id = route.params.id as string
const actionLoading = ref('')

const canManageProduction = computed(() => userStore.hasPermission('can_manage_production'))
const isAdmin = computed(() => userStore.userInfo?.is_superuser === true)

// 相机拍照（对齐销售订单）
const showCamera = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
let cameraStream: MediaStream | null = null

// 工作流步骤（与销售订单对齐）
const step1Done = computed(() =>
  detail.value?.items?.length
    ? detail.value.items.every(i => i.consumed_quantity >= i.quantity)
    : false
)
const step2Done = computed(() => detail.value?.completed_quantity != null)
const step3Done = computed(() => (detail.value?.images?.length ?? 0) > 0)
const step4Ready = computed(() => step1Done.value && step2Done.value && step3Done.value)

// 物料全部检查完成后，产出数量默认设为计划数量
watch(step1Done, (done) => {
  if (done && detail.value) {
    yieldQuantity.value = Number(detail.value.quantity)
  }
})

// 编辑模式
const isEditing = ref(false)
const editLoading = ref(false)
const showProductPicker = ref(false)
const editForm = ref({
  product_id: '',
  product_name: '',
  quantity: 0,
  remark: ''
})

const finishedProductFilter = (item: any) => item.category === 'product'

function selectEditProduct(product: any) {
  editForm.value.product_id = product.id
  editForm.value.product_name = product.name
}

function enterEdit() {
  if (!detail.value) return
  editForm.value = {
    product_id: detail.value.product_id,
    product_name: detail.value.product?.name || '',
    quantity: detail.value.quantity,
    remark: detail.value.remark || ''
  }
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
}

async function handleSaveEdit() {
  if (!editForm.value.product_id) {
    showMessage('请选择产品')
    return
  }
  if (!editForm.value.quantity || editForm.value.quantity <= 0) {
    showMessage('请填写生产数量')
    return
  }

  editLoading.value = true
  try {
    const data: ProductionOrderUpdate = {
      product_id: editForm.value.product_id,
      quantity: editForm.value.quantity,
      remark: editForm.value.remark || undefined
    }
    await updateProductionOrder(id, data)
    showMessage('保存成功，BOM物料已重新生成')
    isEditing.value = false
    fetchDetail()
  } catch (e) {
    showMessage(handleError(e))
  } finally {
    editLoading.value = false
  }
}

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

// 物料分配（标记已消耗，与销售订单物料检查对齐）
async function handleDistributeMaterial(itemId: string) {
  actionLoading.value = itemId
  try {
    await distributeProductionItem(id, itemId)
    showMessage('已检查')
    fetchDetail()
  } catch (e) {
    showMessage(handleError(e))
  } finally {
    actionLoading.value = ''
  }
}

// 确认产出数量
const yieldQuantity = ref(0)
async function handleSetYield() {
  const qty = yieldQuantity.value
  // 校验：必须填写有效数字
  if (qty == null || isNaN(Number(qty)) || qty < 0) {
    showMessage('请填写有效的产出数量（0 或正整数）')
    return
  }
  // 校验：不能超过计划数量
  if (qty > (detail.value?.quantity || 0)) {
    showMessage(`产出数量不得超过计划数量 ${detail.value?.quantity}`)
    return
  }
  // 产出为 0 时弹出二次确认
  if (qty === 0) {
    try {
      await showConfirmDialog({
        title: '确认产出为 0',
        message: '确定本次实际产出数量为 0 吗？确认后表示本次生产没有成功产出产品。',
      })
    } catch {
      return // 用户取消
    }
  }
  actionLoading.value = 'yield'
  try {
    await setProductionYield(id, qty)
    showMessage(qty === 0 ? '已确认产出为 0' : '产出已确认')
    fetchDetail()
  } catch (e) {
    showMessage(handleError(e))
  } finally {
    actionLoading.value = ''
  }
}

// 打开相机
async function openCamera() {
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

// 关闭相机
function closeCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(t => t.stop())
    cameraStream = null
  }
  showCamera.value = false
}

// 拍照并上传
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

  if (file.size > 5 * 1024 * 1024) {
    showMessage('图片过大，请压缩后重试')
    return
  }

  closeCamera()
  actionLoading.value = 'upload'
  try {
    await uploadProductionOrderImage(id, file)
    showMessage('上传成功')
    fetchDetail()
  } catch (e) {
    showMessage(handleError(e))
  } finally {
    actionLoading.value = ''
  }
}

// 删除产品图
async function handleDeleteImage(imageId: string) {
  actionLoading.value = imageId
  try {
    await deleteProductionOrderImage(imageId)
    showMessage('已删除')
    fetchDetail()
  } catch (e) {
    showMessage(handleError(e))
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

// 取消订单（仅管理员，两步确认）
async function handleCancel() {
  // 第一步：确认是否取消
  try {
    await showConfirmDialog({
      title: '取消生产订单',
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
      title: '取消生产订单',
      message: '已扣物料库存是否退回？',
      confirmButtonText: '退回库存并取消',
      cancelButtonText: '不退回直接取消',
    })
  } catch {
    returnInventory = false
  }

  actionLoading.value = 'cancel'
  try {
    await cancelProductionOrder(id, returnInventory)
    showMessage(returnInventory ? '已取消，物料库存已退回' : '已取消，物料库存未退回')
    fetchDetail()
  } catch (e) {
    showMessage(handleError(e))
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
    <van-nav-bar :title="`生产订单｜${detail?.order_no || ''}`" left-arrow @click-left="router.back()">
      <template v-if="detail?.status === 'draft' && !isEditing && canManageProduction" #right>
        <van-icon name="edit" size="20" @click="enterEdit" />
      </template>
    </van-nav-bar>

    <div v-if="detail" class="detail-content">
      <!-- 工作流进度条（仅 pending 状态，放在最顶部） -->
      <div v-if="detail.status === 'pending'" class="workflow-steps full-width">
        <div class="wf-step" :class="{ done: step1Done, active: !step1Done }">
          <div class="wf-step-num">1</div>
          <div class="wf-step-label">{{ step1Done ? '物料已检查' : '检查物料' }}</div>
        </div>
        <div class="wf-line" :class="{ done: step1Done }"></div>
        <div class="wf-step" :class="{ done: step2Done, active: step1Done && !step2Done, locked: !step1Done }">
          <div class="wf-step-num">2</div>
          <div class="wf-step-label">{{ step2Done ? '产出已确认' : '确认产出' }}</div>
        </div>
        <div class="wf-line" :class="{ done: step2Done }"></div>
        <div class="wf-step" :class="{ done: step3Done, active: step2Done && !step3Done, locked: !step2Done }">
          <div class="wf-step-num">3</div>
          <div class="wf-step-label">{{ step3Done ? '产品图已上传' : '上传产品图' }}</div>
        </div>
        <div class="wf-line" :class="{ done: step3Done }"></div>
        <div class="wf-step" :class="{ done: false, active: step4Ready, locked: !step4Ready }">
          <div class="wf-step-num">4</div>
          <div class="wf-step-label">报工完成</div>
        </div>
      </div>

      <div class="detail-grid">
        <!-- 订单信息 -->
        <div class="card">
        <div class="card-title">
          订单信息
          <span v-if="isEditing" class="editing-badge">编辑中</span>
        </div>

        <!-- 编辑模式 -->
        <template v-if="isEditing">
          <van-form @submit="handleSaveEdit">
            <van-field
              v-model="editForm.product_name"
              is-readonly
              clickable
              label="产品"
              placeholder="请选择产品"
              @click="showProductPicker = true"
            />
            <van-field
              v-model.number="editForm.quantity"
              type="digit"
              label="生产数量"
              placeholder="请输入数量"
            />
            <van-field
              v-model="editForm.remark"
              type="textarea"
              label="备注"
              placeholder="请输入备注"
              rows="2"
            />
            <div class="edit-actions">
              <van-button type="primary" size="small" :loading="editLoading" native-type="submit">
                保存
              </van-button>
              <van-button type="default" size="small" @click="cancelEdit">
                取消
              </van-button>
            </div>
          </van-form>
        </template>

        <!-- 查看模式 -->
        <template v-else>
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
              <span v-else>{{ detail.product?.name || '—' }}</span>
            </span>
          </div>
          <div class="info-row">
            <span class="label">生产数量</span>
            <span class="value">{{ Number(detail.quantity) }}</span>
          </div>
          <div class="info-row" v-if="detail.status === 'completed'">
            <span class="label">完成数量</span>
            <span class="value">{{ Number(detail.completed_quantity) }}</span>
          </div>
          <div class="info-row" v-if="detail.remark">
            <span class="label">备注</span>
            <span class="value">{{ detail.remark }}</span>
          </div>
        </template>
      </div>

      <!-- BOM物料（含分配按钮，对齐销售订单物料检查） -->
      <div class="card">
        <div class="card-title">
          <span v-if="detail.status === 'pending' && !step1Done" class="pulse-dot"></span>
          物料需求
          <span v-if="detail.status === 'pending' && step1Done" class="step-done-tag">已全部检查</span>
        </div>
        <div
          v-for="item in detail.items"
          :key="item.id"
          class="material-item"
        >
          <img
            v-if="item.material?.thumbnail_url"
            class="material-thumb"
            :src="item.material.thumbnail_url"
            @click.stop="previewImage(item.material.thumbnail_url)"
          />
          <div v-else class="material-thumb material-thumb-placeholder">
            <van-icon name="photo-o" size="16" />
          </div>
          <div class="material-info">
            <a :href="`/materials/${item.material_id}`" target="_blank" class="link">{{ item.material_name }}</a>
            <div class="material-quantity">
              需求: {{ Number(item.quantity) }}
              <span v-if="item.consumed_quantity > 0" class="consumed-info">
                / 已消耗: {{ Number(item.consumed_quantity) }}
              </span>
            </div>
          </div>
          <div class="material-action">
            <van-button
              v-if="detail.status === 'pending' && item.consumed_quantity < item.quantity"
              size="small"
              class="action-btn-blue"
              :loading="actionLoading === item.id"
              @click="handleDistributeMaterial(item.id)"
            >
              <span class="pulse-dot"></span>
              待检查
            </van-button>
            <span v-else-if="item.consumed_quantity >= item.quantity" class="check-done-tag">已检查</span>
          </div>
        </div>
        <van-empty v-if="!detail.items || detail.items.length === 0" description="暂无物料" />
      </div>

      <!-- 产出数量确认（待生产时未完成显示编辑，已完成显示只读） -->
      <div v-if="(detail.status === 'pending' && step1Done) || detail.status === 'completed'" class="card">
        <div class="card-title">
          <span v-if="detail.status === 'pending' && !step2Done" class="pulse-dot"></span>
          确认实际产出数量
          <span v-if="detail.status === 'completed' || step2Done" class="step-done-tag">已确认</span>
        </div>
        <div class="info-row">
          <span class="label">计划数量</span>
          <span class="value">{{ Number(detail.quantity) }}</span>
        </div>
        <div class="info-row">
          <span class="label">完成数量</span>
          <span class="value">
            <template v-if="detail.status === 'completed' || step2Done">{{ Number(detail.completed_quantity) }}</template>
            <van-stepper
              v-else
              v-model="yieldQuantity"
              :min="0"
              :max="Number(detail.quantity)"
              integer
              theme="round"
            />
          </span>
        </div>
        <template v-if="detail.status === 'pending' && !step2Done">
          <van-button
            type="primary"
            size="small"
            block
            :loading="actionLoading === 'yield'"
            @click="handleSetYield"
            style="margin-top: 8px"
          >
            <span class="pulse-dot"></span>
            确认实际产出数量
          </van-button>
        </template>
      </div>

      <!-- 产品图（待生产时显示上传，完成后只读展示） -->
      <div v-if="(detail.status === 'pending' && step2Done) || detail.status === 'completed'" class="card">
        <div class="card-title">
          <span v-if="detail.status === 'pending' && !step3Done" class="pulse-dot"></span>
          产品图片
          <span v-if="step3Done || detail.status === 'completed'" class="step-done-tag">已上传</span>
          <span class="image-count">{{ detail.images?.length ? `已上传 · ${detail.images.length} 张` : '待上传' }}</span>
        </div>
        <div class="image-upload-row">
          <div
            v-for="img in detail.images"
            :key="img.id"
            class="uploaded-image-wrapper"
          >
            <img :src="img.image_url" class="uploaded-image" @click="previewImage(img.image_url)" />
            <van-icon
              v-if="detail.status === 'pending'"
              name="close"
              class="delete-image-icon"
              @click.stop="handleDeleteImage(img.id)"
            />
          </div>
          <div v-if="detail.status === 'pending'" class="upload-trigger" @click="openCamera">
            <van-icon name="plus" size="24" color="#999" />
            <span class="upload-text"><span v-if="!step3Done" class="pulse-dot"></span>拍照</span>
          </div>
        </div>
      </div>

      <!-- 操作按钮：按状态和角色显示 -->
      <div class="action-btns full-width">
        <!-- 草稿：运营可编辑/删除/发布 -->
        <template v-if="detail.status === 'draft' && canManageProduction">
          <template v-if="!isEditing">
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
        </template>

        <!-- 待生产：按步骤引导完成 -->
        <template v-if="detail.status === 'pending' && canManageProduction">
          <van-button
            v-if="step4Ready"
            size="large"
            class="action-btn-blue action-block"
            round
            :loading="actionLoading === 'complete'"
            @click="handleComplete"
          >
            <span class="pulse-dot"></span>
            报工完成（成品入库）
          </van-button>
          <van-button
            v-else
            size="large"
            class="action-btn-disabled action-block"
            round
            disabled
          >
            {{ !step1Done ? '步骤① 请先检查所有物料' : !step2Done ? '步骤② 请确认产出数量' : '步骤③ 请上传产品图片' }}
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
        </template>

        <!-- 生产中：兼容旧数据，仍可报工 -->
        <template v-if="detail.status === 'in_production' && canManageProduction">
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
          v-if="!canManageProduction"
          description="暂无操作权限，请联系管理员"
        />
      </div>
      </div><!-- .detail-grid -->
    </div>

    <!-- 编辑模式下的产品选择器 -->
    <ProductSelector
      v-model="showProductPicker"
      :filter="finishedProductFilter"
      @select="selectEditProduct"
    />

    <!-- 相机拍照取景器（对齐销售订单） -->
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
  </div>
</template>

<style scoped>
.production-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
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
}

.full-width {
  grid-column: 1 / -1;
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

.action-btn-blue {
  background: #1890ff !important;
  border-color: #1890ff !important;
  color: #fff !important;
}

.action-btn-disabled {
  background: #f5f5f5 !important;
  border-color: #d9d9d9 !important;
  color: #bfbfbf !important;
}

.action-block {
  width: 100%;
}

.editing-badge {
  font-size: 12px;
  color: #e6a23c;
  font-weight: normal;
  margin-left: 8px;
}

.edit-actions {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
}

.edit-actions .van-button {
  flex: 1;
}

/* ========== 工作流步骤（与销售订单对齐） ========== */
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

.step-done-tag {
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
}

.wf-step.done .wf-step-num {
  background: #07c160;
  color: #fff;
}

.wf-step.locked .wf-step-num {
  background: #f5f5f5;
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

.wf-step.locked .wf-step-label {
  color: #ccc;
}

.wf-line {
  width: 32px;
  height: 2px;
  background: #eee;
  margin: 0 4px;
  align-self: flex-start;
  margin-top: 14px;
  transition: background 0.3s ease;
}

.wf-line.done {
  background: #07c160;
}

/* ========== 物料列表 ========== */
.material-thumb {
  width: 36px;
  height: 36px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #eee;
  flex-shrink: 0;
}

.material-thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  color: #ccc;
}

.material-action {
  flex-shrink: 0;
  margin-left: 10px;
}

.action-btn-blue {
  background: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
}

.check-done-tag {
  font-size: 12px;
  color: #07c160;
  font-weight: 500;
}

.consumed-info {
  color: #07c160;
  font-size: 12px;
}

.yield-pending {
  color: #e6a23c;
  font-size: 13px;
}

/* ========== 产品图片上传 ========== */
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

.uploaded-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid #eee;
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

/* ========== 相机取景器（对齐销售订单） ========== */
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
