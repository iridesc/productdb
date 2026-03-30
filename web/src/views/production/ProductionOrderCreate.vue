<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { createProductionOrder } from '@/api/production'
import { getMaterials } from '@/api/material'

const router = useRouter()
const loading = ref(false)

const form = ref({
  product_id: '',
  product_name: '',
  quantity: 1,
  remark: ''
})

const products = ref<any[]>([])
const showPicker = ref(false)

async function loadProducts() {
  try {
    const res: any = await getMaterials({ page_size: 100 })
    products.value = res.items.filter((p: any) => p.is_active && p.category === 'finished_product')
  } catch (e) {
    console.error(e)
  }
}

function onConfirm({ selectedOptions }: any) {
  const product = selectedOptions[0]
  form.value.product_id = product.id
  form.value.product_name = product.name
  showPicker.value = false
}

async function handleSubmit() {
  if (!form.value.product_id) {
    showToast('请选择产品')
    return
  }
  if (!form.value.quantity || form.value.quantity <= 0) {
    showToast('请填写生产数量')
    return
  }

  loading.value = true
  try {
    await createProductionOrder(form.value as any)
    showToast('创建成功')
    router.back()
  } catch (e: any) {
    showToast(e.message || '创建失败')
  } finally {
    loading.value = false
  }
}

loadProducts()
</script>

<template>
  <div class="create-page">
    <van-nav-bar title="创建生产订单" left-arrow @click-left="router.back()" />

    <van-form @submit="handleSubmit">
      <van-cell-group inset title="生产信息">
        <van-field
          v-model="form.product_name"
          is-readonly
          clickable
          label="产品"
          placeholder="请选择产品"
          @click="showPicker = true"
        />
        <van-field
          v-model.number="form.quantity"
          type="digit"
          label="生产数量"
          placeholder="请输入数量"
        />
        <van-field
          v-model="form.remark"
          type="textarea"
          label="备注"
          placeholder="请输入备注"
          rows="2"
        />
      </van-cell-group>

      <div class="submit-btn">
        <van-button type="primary" size="large" :loading="loading" native-type="submit">
          提交
        </van-button>
      </div>
    </van-form>

    <van-popup v-model:show="showPicker" position="bottom" round>
      <van-picker
        title="选择产品"
        :columns="products.map(p => ({ text: p.name, value: p.id }))"
        @confirm="onConfirm"
        @cancel="showPicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.create-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.submit-btn {
  padding: 16px;
}
</style>