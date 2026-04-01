<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showMessage } from '@/utils/request'
import { createProductionOrder } from '@/api/production'
import { handleError } from '@/utils/request'
import ProductSelector from '@/components/ProductSelector.vue'

const router = useRouter()
const loading = ref(false)

const form = ref({
  product_id: '',
  product_name: '',
  quantity: 1,
  remark: ''
})

const showProductPicker = ref(false)

function selectProduct(product: any) {
  form.value.product_id = product.id
  form.value.product_name = product.name
}

const finishedProductFilter = (item: any) => item.category === 'finished_product'

async function handleSubmit() {
  if (!form.value.product_id) {
    showMessage('请选择产品')
    return
  }
  if (!form.value.quantity || form.value.quantity <= 0) {
    showMessage('请填写生产数量')
    return
  }

  loading.value = true
  try {
    await createProductionOrder(form.value as any)
    showMessage('创建成功')
    router.back()
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    loading.value = false
  }
}
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
          @click="showProductPicker = true"
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

    <!-- 产品选择器（带搜索） -->
    <ProductSelector
      v-model="showProductPicker"
      :filter="finishedProductFilter"
      @select="selectProduct"
    />
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