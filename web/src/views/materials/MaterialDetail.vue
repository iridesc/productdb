<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { getMaterial, updateMaterial, deleteMaterial, getMaterials } from '@/api/material'
import { getProductBOM, createBOM, updateBOM, deleteBOM, type BOMItem } from '@/api/bom'
import type { Material, MaterialCategory } from '@/types/material'

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
    showToast('请填写名称')
    return
  }

  loading.value = true
  try {
    await updateMaterial(id, form.value as any)
    showToast('保存成功')
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
    showToast('删除成功')
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
    showToast('请选择物料')
    return
  }
  if (bomForm.value.quantity <= 0) {
    showToast('数量必须大于0')
    return
  }

  try {
    if (editingBOM.value) {
      await updateBOM(editingBOM.value.id, {
        quantity: bomForm.value.quantity,
        scrap_rate: bomForm.value.scrap_rate,
        note: bomForm.value.note
      })
      showToast('更新成功')
    } else {
      await createBOM({
        product_id: id,
        material_id: bomForm.value.material_id,
        quantity: bomForm.value.quantity,
        scrap_rate: bomForm.value.scrap_rate,
        note: bomForm.value.note
      })
      showToast('添加成功')
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
    showToast('删除成功')
    await fetchBOM()
  } catch (e) {
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="material-detail-page">
    <van-nav-bar title="物料详情" left-arrow @click-left="router.back()">
      <template #right>
        <div class="nav-actions">
          <van-icon v-if="!isEditing" name="edit" size="20" @click="handleEdit" style="margin-right: 16px" />
          <van-icon v-if="!isEditing" name="delete-o" size="20" @click="handleDelete" />
        </div>
      </template>
    </van-nav-bar>

    <div v-if="detail" class="detail-content">
      <template v-if="!isEditing">
        <div class="card">
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

        <div class="card">
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

        <div class="card">
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

        <div v-if="detail.description" class="card">
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
      </template>

      <template v-else>
        <van-form @submit="handleSave">
          <van-cell-group inset title="基本信息">
            <van-field v-model="detail.code" name="code" label="物料编码" readonly />
            <van-field v-model="form.name" name="name" label="物料名称" placeholder="请输入名称"
              :rules="[{ required: true, message: '请输入名称' }]" />
            <van-field v-model="currentCategoryText" is-link readonly name="category" label="物料分类" placeholder="请选择分类"
              @click="showCategoryPicker = true" />
            <van-field v-model="form.unit" is-link readonly name="unit" label="单位" placeholder="请选择单位"
              @click="showUnitPicker = true" />
            <van-field v-model="form.description" type="textarea" name="description" label="描述" placeholder="请输入描述"
              rows="3" />
          </van-cell-group>

          <van-cell-group inset title="成本信息">
            <van-field v-model.number="form.sale_price" type="number" name="sale_price" label="售价" placeholder="销售价格" />
            <van-field v-model.number="form.price" type="number" name="price" label="基础单价" placeholder="基础采购单价" />
            <van-field v-model.number="form.other_cost" type="number" name="other_cost" label="其他成本"
              placeholder="其他成本" />
          </van-cell-group>

          <van-cell-group inset title="库存信息">
            <van-field v-model.number="form.current_stock" type="number" name="current_stock" label="当前库存"
              placeholder="当前库存数量" />
            <van-field v-model.number="form.safety_stock" type="number" name="safety_stock" label="安全库存"
              placeholder="低于此值预警" />
          </van-cell-group>

          <div class="edit-btns">
            <van-button type="default" block @click="handleCancel">取消</van-button>
            <van-button type="primary" block native-type="submit" :loading="loading">保存</van-button>
          </div>
        </van-form>
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
</style>
