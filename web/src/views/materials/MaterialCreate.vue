<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast } from 'vant'
import { createMaterial } from '@/api/material'

const router = useRouter()

const loading = ref(false)
const form = ref({
  code: '',
  name: '',
  category: 'finished_product' as const,
  unit: '个',
  specification: '',
  safety_stock: 0,
  price: 0,
  description: ''
})

const categoryOptions = [
  { text: '成品', value: 'finished_product' },
  { text: '半成品', value: 'semi_finished' },
  { text: '原材料', value: 'raw_material' },
  { text: '辅料', value: 'auxiliary' }
]

async function handleSubmit() {
  if (!form.value.code || !form.value.name) {
    showToast('请填写必填项')
    return
  }
  
  loading.value = true
  try {
    await createMaterial(form.value as any)
    showToast('创建成功')
    router.back()
  } catch (e: any) {
    showToast(e.message || '创建失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="material-create-page">
    <van-nav-bar 
      title="创建物料" 
      left-arrow 
      @click-left="router.back()"
    />

    <van-form @submit="handleSubmit">
      <van-cell-group inset>
        <van-field
          v-model="form.code"
          name="code"
          label="物料编码"
          placeholder="请输入编码"
          :rules="[{ required: true, message: '请输入编码' }]"
        />
        <van-field
          v-model="form.name"
          name="name"
          label="物料名称"
          placeholder="请输入名称"
          :rules="[{ required: true, message: '请输入名称' }]"
        />
        <van-field
          v-model="form.category"
          is-readonly
          clickable
          name="category"
          label="物料分类"
          placeholder="请选择分类"
          @click="showPicker = true"
        />
        <van-field
          v-model="form.unit"
          name="unit"
          label="单位"
          placeholder="如：个、箱、个"
        />
        <van-field
          v-model="form.specification"
          name="specification"
          label="规格型号"
          placeholder="请输入规格"
        />
        <van-field
          v-model.number="form.safety_stock"
          type="digit"
          name="safety_stock"
          label="安全库存"
          placeholder="低于此值预警"
        />
        <van-field
          v-model.number="form.price"
          type="digit"
          name="price"
          label="单价"
          placeholder="销售价格"
        />
        <van-field
          v-model="form.description"
          type="textarea"
          name="description"
          label="描述"
          placeholder="请输入描述"
          rows="3"
        />
      </van-cell-group>

      <div class="submit-btn">
        <van-button
          type="primary"
          size="large"
          :loading="loading"
          native-type="submit"
        >
          提交
        </van-button>
      </div>
    </van-form>
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