<script setup lang="ts">
import { ref, watch } from 'vue'
import { showMessage } from '@/utils/request'
import { getMaterials } from '@/api/material'
import { handleError } from '@/utils/request'

const props = defineProps<{
  modelValue: boolean
  multiple?: boolean
  filter?: (item: any) => boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'select': [product: any]
  'select-multiple': [products: any[]]
}>()

const products = ref<any[]>([])
const searchKeyword = ref('')
const loading = ref(false)

async function loadProducts(keyword?: string) {
  loading.value = true
  try {
    const params: any = { page_size: 100, is_active: true }
    if (keyword) {
      params.keyword = keyword
    }
    const res: any = await getMaterials(params)
    let items = res.items || []
    if (props.filter) {
      items = items.filter(props.filter)
    }
    products.value = items
  } catch (e) {
    const errorMessage = handleError(e)
    showMessage(errorMessage)
  } finally {
    loading.value = false
  }
}

let searchTimer: any = null
function handleSearch(value: string) {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadProducts(value)
  }, 300)
}

watch(() => props.modelValue, (val) => {
  if (val) {
    searchKeyword.value = ''
    loadProducts()
  }
})

function selectProduct(product: any) {
  if (props.multiple) {
    emit('select-multiple', [product])
  } else {
    emit('select', product)
    emit('update:modelValue', false)
  }
}
</script>

<template>
  <van-popup :show="modelValue" @update:show="emit('update:modelValue', $event)" position="bottom" round style="height: 70%">
    <div class="product-picker-header">
      <div class="picker-title">选择产品</div>
      <van-icon name="cross" @click="emit('update:modelValue', false)" />
    </div>

    <van-search
      v-model="searchKeyword"
      placeholder="搜索物料名称或编码"
      @update:model-value="handleSearch"
      @search="handleSearch(searchKeyword)"
    />

    <div class="product-list-container">
      <van-loading v-if="loading" class="loading-center" />
      <van-empty v-else-if="products.length === 0" description="暂无产品" />
      <div
        v-for="product in products"
        :key="product.id"
        class="product-item"
        @click="selectProduct(product)"
      >
        <div class="product-item-info">
          <div class="product-item-name">{{ product.name }}</div>
          <div class="product-item-code">编码：{{ product.code }}</div>
        </div>
        <div class="product-item-price">¥{{ product.price || 0 }}</div>
      </div>
    </div>
  </van-popup>
</template>

<style scoped>
.product-picker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.picker-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.product-list-container {
  height: calc(70vh - 120px);
  overflow-y: auto;
  padding: 8px 0;
}

.product-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background-color 0.2s;
}

.product-item:active {
  background-color: #f5f5f5;
}

.product-item-info {
  flex: 1;
}

.product-item-name {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.product-item-code {
  font-size: 12px;
  color: #999;
}

.product-item-price {
  font-size: 14px;
  color: #ff4d4f;
  font-weight: 500;
  margin-left: 12px;
}

.loading-center {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}
</style>
