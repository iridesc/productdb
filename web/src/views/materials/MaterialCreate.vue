<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showMessage } from '@/utils/request'
import { createMaterial } from '@/api/material'

const router = useRouter()

const loading = ref(false)
const showCategoryPicker = ref(false)
const showUnitPicker = ref(false)
const form = ref({
  code: '',
  name: '',
  category: 'finished_product' as const,
  unit: '个',
  safety_stock: 1,
  price: 0,
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

const currentCategoryText = computed(() => {
  const option = categoryOptions.find(opt => opt.value === form.value.category)
  return option ? option.text : ''
})

function onCategoryConfirm(value: any) {
  form.value.category = value.selectedOptions[0].value
  showCategoryPicker.value = false
}

function onUnitConfirm(value: any) {
  form.value.unit = value.selectedOptions[0].value
  showUnitPicker.value = false
}

async function handleSubmit() {
  if (!form.value.code || !form.value.name) {
    showMessage('请填写必填项')
    return
  }

  loading.value = true
  try {
    await createMaterial(form.value as any)
    showMessage('创建成功')
    router.back()
  } catch (e: any) {
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="material-create-page">
    <van-nav-bar title="创建物料" left-arrow @click-left="router.back()" />

    <van-form @submit="handleSubmit">
      <van-cell-group inset>
        <van-field v-model="form.code" name="code" label="物料编码" placeholder="请输入编码"
          :rules="[{ required: true, message: '请输入编码' }]" />
        <van-field v-model="form.name" name="name" label="物料名称" placeholder="请输入名称"
          :rules="[{ required: true, message: '请输入名称' }]" />
        <van-field v-model="currentCategoryText" is-link readonly name="category" label="物料分类" placeholder="请选择分类"
          @click="showCategoryPicker = true" />
        <van-field v-model="form.unit" is-link readonly name="unit" label="单位" placeholder="请选择单位"
          @click="showUnitPicker = true" />
        <van-field v-model.number="form.safety_stock" type="digit" name="safety_stock" label="安全库存"
          placeholder="低于此值预警" />
        <van-field v-model.number="form.price" type="digit" name="price" label="单价" placeholder="销售价格" />
        <van-field v-model="form.description" type="textarea" name="description" label="描述" placeholder="请输入描述"
          rows="3" />
      </van-cell-group>

      <div class="submit-btn">
        <van-button type="primary" size="large" :loading="loading" native-type="submit">
          提交
        </van-button>
      </div>
    </van-form>

    <van-popup v-model:show="showCategoryPicker" position="bottom" round>
      <van-picker title="选择物料分类" :columns="categoryOptions" @confirm="onCategoryConfirm"
        @cancel="showCategoryPicker = false" />
    </van-popup>

    <van-popup v-model:show="showUnitPicker" position="bottom" round>
      <van-picker title="选择单位" :columns="unitOptions" @confirm="onUnitConfirm" @cancel="showUnitPicker = false" />
    </van-popup>
  </div>
</template>

<style scoped>
.material-create-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.submit-btn {
  padding: 16px;
}
</style>