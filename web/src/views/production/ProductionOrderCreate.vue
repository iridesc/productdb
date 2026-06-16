<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showMessage } from '@/utils/request'
import { createProductionOrder } from '@/api/production'
import { handleError } from '@/utils/request'
import ProductSelector from '@/components/ProductSelector.vue'
import { useUserStore } from '@/store/user'

const router = useRouter()
const userStore = useUserStore()
const hasPermission = computed(() => userStore.hasPermission('can_create_production'))
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

const finishedProductFilter = (item: any) => item.category === 'product'

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
    showMessage('草稿创建成功，请确认物料库存后发布')
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
    <template v-if="hasPermission">
    <van-nav-bar title="创建生产订单" left-arrow @click-left="router.back()" />

    <van-notice-bar
      left-icon="info-o"
      color="#1989fa"
      background="#ecf5ff"
      text="创建后将生成草稿，需在详情页确认库存后发布。"
      wrapable
    />

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
          创建草稿
        </van-button>
      </div>
    </van-form>

    <!-- 产品选择器（带搜索） -->
    <ProductSelector
      v-model="showProductPicker"
      :filter="finishedProductFilter"
      @select="selectProduct"
    />
    </template>
    <van-empty v-else description="暂无权限，请联系管理员" />
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
