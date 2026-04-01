<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog } from 'vant'
import { getMaterial, updateMaterial, deleteMaterial, getMaterials } from '@/api/material'
import { getProductBOM, createBOM, updateBOM, deleteBOM, type BOMItem } from '@/api/bom'
import { getMaterialImages, uploadMaterialImage, deleteMaterialImage, type MaterialImage } from '@/api/image'
import { getProductionOrders, createProductionOrder } from '@/api/production'
import type { Material, MaterialCategory } from '@/types/material'
import type { ProductionOrder } from '@/types/production'
import { showMessage, handleError } from '@/utils/request'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const detail = ref<Material | null>(null)
const isEditing = ref(false)
const showCategoryPicker = ref(false)
const showUnitPicker = ref(false)
const id = route.params.id as string

const form = ref({
  name: '',
  category: 'finished_product' as MaterialCategory,
  unit: '个',
  safety_stock: 1,
  current_stock: 0,
  price: 0,
  sale_price: 0,
  other_cost: 0,
  description: ''
})

const categoryOptions = [
  { text: '成品', value: 'finished_product' },
  { text: '半成品', value: 'semi_finished' },
  { text: '原材料', value: 'raw_material' },
  { text: '辅料', value: 'auxiliary' }
]

const unitOptions = [
  { text: '个', value: '个' },
  { text: '件', value: '件' },
  { text: '箱', value: '箱' },
  { text: '套', value: '套' },
  { text: 'kg', value: 'kg' },
  { text: '米', value: '米' },
  { text: '升', value: '升' }
]

const categoryMap: Record<string, string> = {
  finished_product: '成品',
  semi_finished: '半成品',
  raw_material: '原材料',
  auxiliary: '辅料'
}

const poStatusMap: Record<string, string> = {
  pending: '待生产',
  in_production: '生产中',
  completed: '已完成',
  cancelled: '已取消'
}

function statusText(status: string) {
  return poStatusMap[status] || status
}

const currentCategoryText = computed(() => {
  const option = categoryOptions.find(opt => opt.value === form.value.category)
  return option ? option.text : ''
})

const bomList = ref<BOMItem[]>([])
const showBOMEdit = ref(false)
const editingBOM = ref<BOMItem | null>(null)
const bomForm = ref({
  material_id: '',
  material_name: '',
  quantity: 1,
  scrap_rate: 0,
  note: ''
})

const showMaterialPicker = ref(false)
const materialOptions = ref<{ text: string; value: string }[]>([])
const allMaterials = ref<Material[]>([])

const imageList = ref<MaterialImage[]>([])
const uploading = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const showPreview = ref(false)
const previewUrl = ref('')

const productionOrders = ref<ProductionOrder[]>([])
const showCreatePO = ref(false)
const poCreating = ref(false)
const poForm = ref({
  quantity: 1,
  remark: ''
})

async function fetchDetail() {
  loading.value = true
  try {
    detail.value = await getMaterial(id) as any
    if (detail.value) {
      form.value = {
        name: detail.value.name,
        category: detail.value.category,
        unit: detail.value.unit,
        safety_stock: Number(detail.value.safety_stock),
        current_stock: Number(detail.value.current_stock),
        price: Number(detail.value.price),
        sale_price: Number(detail.value.sale_price) || 0,
        other_cost: Number(detail.value.other_cost) || 0,
        description: detail.value.description || ''
      }
    }
    await fetchBOM()
    await fetchImages()
    await fetchProductionOrders()
  } catch (e) {
  } finally {
    loading.value = false
  }
}

async function fetchBOM() {
  try {
    bomList.value = await getProductBOM(id)
  } catch (e) {
    bomList.value = []
  }
}

async function fetchImages() {
  try {
    imageList.value = await getMaterialImages(id)
  } catch (e) {
    imageList.value = []
  }
}

async function fetchProductionOrders() {
  try {
    const res = await getProductionOrders({ page: 1, page_size: 5, product_id: id })
    productionOrders.value = res.items || []
  } catch (e) {
    productionOrders.value = []
  }
}

function openCreatePO() {
  poForm.value = { quantity: 1, remark: '' }
  showCreatePO.value = true
}

async function handleCreatePO() {
  if (!poForm.value.quantity || poForm.value.quantity <= 0) {
    showMessage('请填写生产数量')
    return
  }

  poCreating.value = true
  try {
    await createProductionOrder({
      product_id: id,
      quantity: poForm.value.quantity,
      remark: poForm.value.remark || undefined
    })
    showMessage('创建成功')
    showCreatePO.value = false
    await fetchProductionOrders()
  } catch (e) {
  } finally {
    poCreating.value = false
  }
}

async function fetchMaterials() {
  try {
    const res = await getMaterials({ page: 1, page_size: 100 })
    allMaterials.value = res.items || []
    materialOptions.value = (res.items || [])
      .filter((m: Material) => m.id !== id)
      .map((m: Material) => ({
        text: `${m.code} - ${m.name}`,
        value: m.id
      }))
  } catch (e) {
  }
}

function onCategoryConfirm(value: any) {
  form.value.category = value.selectedOptions[0].value
  showCategoryPicker.value = false
}

function onUnitConfirm(value: any) {
  form.value.unit = value.selectedOptions[0].value
  showUnitPicker.value = false
}

function handleEdit() {
  isEditing.value = true
  fetchMaterials()
}

async function handleSave() {
  if (!form.value.name) {
    showMessage('请填写名称')
    return
  }

  loading.value = true
  try {
    await updateMaterial(id, form.value as any)
    showMessage('保存成功')
    isEditing.value = false
    await fetchDetail()
  } catch (e) {
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  isEditing.value = false
  if (detail.value) {
    form.value = {
      name: detail.value.name,
      category: detail.value.category,
      unit: detail.value.unit,
      safety_stock: Number(detail.value.safety_stock),
      current_stock: Number(detail.value.current_stock),
      price: Number(detail.value.price),
      sale_price: Number(detail.value.sale_price) || 0,
      other_cost: Number(detail.value.other_cost) || 0,
      description: detail.value.description || ''
    }
  }
}

async function handleDelete() {
  await showConfirmDialog({
    title: '确认删除',
    message: '确定要删除这个物料吗？'
  })

  try {
    await deleteMaterial(id)
    showMessage('删除成功')
    router.back()
  } catch (e) {
  }
}

function openAddBOM() {
  editingBOM.value = null
  bomForm.value = {
    material_id: '',
    material_name: '',
    quantity: 1,
    scrap_rate: 0,
    note: ''
  }
  fetchMaterials()
  showBOMEdit.value = true
}

function openEditBOM(bom: BOMItem) {
  editingBOM.value = bom
  bomForm.value = {
    material_id: bom.material_id,
    material_name: bom.material_name,
    quantity: Number(bom.quantity),
    scrap_rate: Number(bom.scrap_rate),
    note: bom.note || ''
  }
  showBOMEdit.value = true
}

function onMaterialConfirm(value: any) {
  bomForm.value.material_id = value.selectedOptions[0].value
  bomForm.value.material_name = value.selectedOptions[0].text
  showMaterialPicker.value = false
}

async function saveBOM() {
  if (!bomForm.value.material_id) {
    showMessage('请选择物料')
    return
  }
  if (bomForm.value.quantity <= 0) {
    showMessage('数量必须大于0')
    return
  }

  try {
    if (editingBOM.value) {
      await updateBOM(editingBOM.value.id, {
        quantity: bomForm.value.quantity,
        scrap_rate: bomForm.value.scrap_rate,
        note: bomForm.value.note
      })
      showMessage('更新成功')
    } else {
      await createBOM({
        product_id: id,
        material_id: bomForm.value.material_id,
        quantity: bomForm.value.quantity,
        scrap_rate: bomForm.value.scrap_rate,
        note: bomForm.value.note
      })
      showMessage('添加成功')
    }
    showBOMEdit.value = false
    await fetchBOM()
  } catch (e) {
  }
}

async function deleteBOMItem(bom: BOMItem) {
  await showConfirmDialog({
    title: '确认删除',
    message: `确定要从BOM中移除 ${bom.material_name} 吗？`
  })

  try {
    await deleteBOM(bom.id)
    showMessage('删除成功')
    await fetchBOM()
  } catch (e) {
  }
}

async function handleUploadImage(event: Event) {
  const input = event.target as HTMLInputElement
  
  if (!input.files || !input.files.length) {
    return
  }

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

  uploading.value = true
  try {
    await uploadMaterialImage(id, file)
    showMessage('上传成功')
    await fetchImages()
  } catch (e: any) {
    await showConfirmDialog({
      title: '上传失败',
      message: e?.response?.data?.detail || '上传失败，请重试',
      showCancelButton: false
    })
  } finally {
    uploading.value = false
    input.value = ''
  }
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function previewImage(index: number) {
  previewUrl.value = imageList.value[index].image_url
  showPreview.value = true
}

function closePreview() {
  showPreview.value = false
  previewUrl.value = ''
}

async function handleDeleteImage(image: MaterialImage) {
  await showConfirmDialog({
    title: '确认删除',
    message: '确定要删除这张图片吗？'
  })

  try {
    await deleteMaterialImage(image.id)
    showMessage('删除成功')
    await fetchImages()
  } catch (e) {
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="material-detail-page">
    <van-nav-bar :title="`物料｜${detail?.name || ''}`" left-arrow @click-left="router.back()">
      <template #right>
        <div class="nav-actions">
          <van-icon v-if="!isEditing" name="edit" size="20" @click="handleEdit" style="margin-right: 16px" />
          <van-icon v-if="!isEditing" name="delete-o" size="20" @click="handleDelete" />
        </div>
      </template>
    </van-nav-bar>

    <div v-if="detail" class="detail-content">
      <div class="detail-grid">
        <div class="card image-card">
          <div class="card-header">
            <div class="card-title">图片</div>
            <div v-if="isEditing" class="upload-btn" :class="{ uploading }" @click="triggerFileInput">
              <van-icon name="photograph" size="18" />
              <span>{{ uploading ? '上传中...' : '上传图片' }}</span>
            </div>
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              @change="handleUploadImage"
              :disabled="uploading"
              style="display: none"
            />
          </div>
          <div v-if="imageList.length === 0" class="empty-text">暂无图片</div>
          <div class="image-grid">
            <div v-for="(image, index) in imageList" :key="image.id" class="image-item">
              <img :src="image.image_url" alt="物料图片" @click="previewImage(index)" />
              <div v-if="isEditing" class="image-delete" @click.stop="handleDeleteImage(image)">
                <van-icon name="close" size="12" color="#fff" />
              </div>
            </div>
          </div>
        </div>

        <template v-if="!isEditing">
          <div class="card info-card">
            <div class="card-title">基本信息</div>
            <div class="info-row">
              <span class="label">编码</span>
              <span class="value">{{ detail.code }}</span>
            </div>
            <div class="info-row">
              <span class="label">名称</span>
              <span class="value">{{ detail.name }}</span>
            </div>
            <div class="info-row">
              <span class="label">分类</span>
              <span class="value">{{ categoryMap[detail.category] || detail.category }}</span>
            </div>
            <div class="info-row">
              <span class="label">单位</span>
              <span class="value">{{ detail.unit }}</span>
            </div>
          </div>

          <div class="card cost-card">
            <div class="card-title">成本信息</div>
            <div class="info-row">
              <span class="label">售价</span>
              <span class="value price">¥{{ detail.sale_price || 0 }}</span>
            </div>
            <div class="info-row">
              <span class="label">物料成本</span>
              <span class="value">¥{{ detail.bom_cost || 0 }}</span>
            </div>
            <div class="info-row">
              <span class="label">其他成本</span>
              <span class="value">¥{{ detail.other_cost || 0 }}</span>
            </div>
            <div class="info-row total-cost">
              <span class="label">总成本</span>
              <span class="value">¥{{ detail.total_cost || 0 }}</span>
            </div>
          </div>

          <div class="card stock-card">
            <div class="card-title">库存信息</div>
            <div class="info-row">
              <span class="label">当前库存</span>
              <span class="value" :class="{ 'low-stock': detail.current_stock < detail.safety_stock }">
                {{ detail.current_stock }} {{ detail.unit }}
              </span>
            </div>
            <div class="info-row">
              <span class="label">安全库存</span>
              <span class="value">{{ detail.safety_stock }} {{ detail.unit }}</span>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="card edit-card">
            <div class="card-title">编辑信息</div>
            <van-form @submit="handleSave">
              <van-field v-model="form.name" name="name" label="名称" placeholder="请输入名称" />
              <van-field v-model="currentCategoryText" is-link readonly name="category" label="分类" placeholder="请选择分类"
                @click="showCategoryPicker = true" />
              <van-field v-model="form.unit" is-link readonly name="unit" label="单位" placeholder="请选择单位"
                @click="showUnitPicker = true" />
              <van-field v-model.number="form.sale_price" type="number" name="sale_price" label="售价" placeholder="销售价格" />
              <van-field v-model.number="form.price" type="number" name="price" label="基础单价" placeholder="基础采购单价" />
              <van-field v-model.number="form.other_cost" type="number" name="other_cost" label="其他成本" placeholder="其他成本" />
              <van-field v-model.number="form.current_stock" type="number" name="current_stock" label="当前库存" placeholder="当前库存数量" />
              <van-field v-model.number="form.safety_stock" type="number" name="safety_stock" label="安全库存" placeholder="低于此值预警" />
              <van-field v-model="form.description" type="textarea" name="description" label="描述" placeholder="请输入描述" rows="3" />
              <div class="edit-btns">
                <van-button type="default" block @click="handleCancel">取消</van-button>
                <van-button type="primary" block native-type="submit" :loading="loading">保存</van-button>
              </div>
            </van-form>
          </div>
        </template>
      </div>

      <template v-if="!isEditing">
        <div v-if="detail.description" class="card full-width">
          <div class="card-title">描述</div>
          <div class="description">{{ detail.description }}</div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">物料清单 (BOM)</div>
            <van-button size="small" type="primary" @click="openAddBOM">添加</van-button>
          </div>
          <div v-if="bomList.length === 0" class="empty-text">暂无BOM数据</div>
          <div v-for="bom in bomList" :key="bom.id" class="bom-item">
            <div class="bom-info">
              <div class="bom-name">{{ bom.material_name }}</div>
              <div class="bom-code">{{ bom.material_code }}</div>
            </div>
            <div class="bom-qty">{{ bom.quantity }} {{ detail.unit }}</div>
            <div class="bom-actions">
              <van-icon name="edit" size="18" @click="openEditBOM(bom)" />
              <van-icon name="delete-o" size="18" @click="deleteBOMItem(bom)" />
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">生产订单（最近5个）</div>
            <van-button size="small" type="primary" @click="openCreatePO">
              <van-icon name="plus" size="12" style="margin-right: 4px" />创建
            </van-button>
          </div>
          <div v-if="productionOrders.length === 0" class="empty-text">暂无生产订单</div>
          <div v-for="po in productionOrders" :key="po.id" class="po-item" @click="router.push(`/production-orders/${po.id}`)">
            <div class="po-info">
              <div class="po-no">{{ po.order_no }}</div>
              <div class="po-qty">数量: {{ po.quantity }} {{ detail.unit }}</div>
            </div>
            <div class="po-status" :class="'status-' + po.status">{{ statusText(po.status) }}</div>
            <van-icon name="arrow" size="16" color="#999" />
          </div>
        </div>
      </template>
    </div>

    <van-popup v-model:show="showCategoryPicker" position="bottom" round>
      <van-picker title="选择物料分类" :columns="categoryOptions" @confirm="onCategoryConfirm"
        @cancel="showCategoryPicker = false" />
    </van-popup>

    <van-popup v-model:show="showUnitPicker" position="bottom" round>
      <van-picker title="选择单位" :columns="unitOptions" @confirm="onUnitConfirm" @cancel="showUnitPicker = false" />
    </van-popup>

    <van-popup v-model:show="showBOMEdit" position="bottom" round style="height: 60%">
      <div class="bom-edit-popup">
        <div class="popup-title">{{ editingBOM ? '编辑BOM项' : '添加BOM项' }}</div>
        <van-form @submit="saveBOM">
          <van-field v-if="!editingBOM" v-model="bomForm.material_name" is-link readonly name="material" label="选择物料"
            placeholder="点击选择物料" @click="showMaterialPicker = true" :rules="[{ required: true, message: '请选择物料' }]" />
          <van-field v-else :model-value="bomForm.material_name" name="material" label="物料" readonly />
          <van-field v-model.number="bomForm.quantity" type="number" name="quantity" label="数量" placeholder="所需数量"
            :rules="[{ required: true, message: '请输入数量' }]" />
          <van-field v-model.number="bomForm.scrap_rate" type="number" name="scrap_rate" label="损耗率(%)"
            placeholder="损耗率" />
          <van-field v-model="bomForm.note" name="note" label="备注" placeholder="备注信息" />
          <div class="popup-btns">
            <van-button type="default" block @click="showBOMEdit = false">取消</van-button>
            <van-button type="primary" block native-type="submit">保存</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>

    <van-popup v-model:show="showMaterialPicker" position="bottom" round>
      <van-picker title="选择物料" :columns="materialOptions" @confirm="onMaterialConfirm"
        @cancel="showMaterialPicker = false" />
    </van-popup>

    <van-popup v-model:show="showCreatePO" position="bottom" round style="height: auto">
      <div class="po-create-popup">
        <div class="popup-title">创建生产订单</div>
        <div class="po-product-info">
          <span class="po-product-label">产品：</span>
          <span class="po-product-name">{{ detail?.name }}</span>
        </div>
        <van-form @submit="handleCreatePO">
          <van-field v-model.number="poForm.quantity" type="digit" label="生产数量" placeholder="请输入数量"
            :rules="[{ required: true, message: '请输入数量' }]" />
          <van-field v-model="poForm.remark" type="textarea" label="备注" placeholder="请输入备注（可选）" rows="2" />
          <div class="popup-btns">
            <van-button type="default" block @click="showCreatePO = false">取消</van-button>
            <van-button type="primary" block native-type="submit" :loading="poCreating">创建</van-button>
          </div>
        </van-form>
      </div>
    </van-popup>

    <div v-if="showPreview" class="image-preview-overlay" @click="closePreview">
      <img :src="previewUrl" alt="预览图片" @click.stop />
      <div class="preview-close" @click="closePreview">✕</div>
    </div>
  </div>
</template>

<style scoped>
.material-detail-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.nav-actions {
  display: flex;
  align-items: center;
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

  .image-card {
    grid-row: span 2;
  }
  
  .full-width {
    grid-column: 1 / -1;
  }
}

@media (min-width: 1200px) {
  .detail-grid {
    grid-template-columns: 1fr 1fr 1fr;
  }

  .image-card {
    grid-row: span 3;
  }
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
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
}

.value.low-stock {
  color: #ff4d4f;
}

.value.price {
  color: #1890ff;
  font-weight: 500;
}

.total-cost {
  background: #f5f5f5;
  margin: 0 -16px;
  padding: 10px 16px;
}

.total-cost .label,
.total-cost .value {
  font-weight: 600;
  color: #333;
}

.description {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

.edit-btns {
  display: flex;
  gap: 12px;
  padding: 16px;
}

.edit-btns .van-button {
  flex: 1;
}

.empty-text {
  color: #999;
  font-size: 14px;
  text-align: center;
  padding: 20px 0;
}

.bom-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
}

.bom-item:last-child {
  border-bottom: none;
}

.bom-info {
  flex: 1;
}

.bom-name {
  font-size: 14px;
  color: #333;
}

.bom-code {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.bom-qty {
  font-size: 14px;
  color: #333;
  margin-right: 12px;
}

.bom-actions {
  display: flex;
  gap: 12px;
  color: #666;
}

.bom-edit-popup {
  padding: 16px;
}

.popup-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  text-align: center;
  margin-bottom: 16px;
}

.popup-btns {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.popup-btns .van-button {
  flex: 1;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: #1890ff;
  color: #fff;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.upload-btn:hover {
  opacity: 0.85;
}

.upload-btn.uploading {
  background: #999;
  cursor: not-allowed;
}

.image-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.image-item {
  position: relative;
  height: 180px;
  border-radius: 8px;
  overflow: hidden;
  background: #f5f5f5;
}

.image-item img {
  width: auto;
  height: 100%;
  max-width: 100%;
  object-fit: contain;
  cursor: pointer;
  display: block;
}

.image-delete {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.image-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.image-preview-overlay img {
  max-width: 95vw;
  max-height: 95vh;
  object-fit: contain;
}

.preview-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  cursor: pointer;
}

.po-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
}

.po-item:last-child {
  border-bottom: none;
}

.po-info {
  flex: 1;
}

.po-no {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.po-qty {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.po-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 8px;
  white-space: nowrap;
}

.status-pending {
  background: #fff7e6;
  color: #fa8c16;
}

.status-in_production {
  background: #e6f7ff;
  color: #1890ff;
}

.status-completed {
  background: #f6ffed;
  color: #52c41a;
}

.status-cancelled {
  background: #fff1f0;
  color: #ff4d4f;
}

.po-create-popup {
  padding: 16px;
}

.po-product-info {
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 6px;
  margin-bottom: 16px;
}

.po-product-label {
  color: #999;
  font-size: 13px;
}

.po-product-name {
  color: #333;
  font-size: 14px;
  font-weight: 600;
}
</style>
