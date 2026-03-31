<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { createSalesOrder } from '@/api/sales'
import { getMaterials } from '@/api/material'

const router = useRouter()
const loading = ref(false)

// 表单数据
const form = ref({
  customer_name: '',
  customer_address: '',
  express_no: '',
  remark: '',
  items: [] as any[],
  order_date: new Date().toISOString().split('T')[0]
})

// 商品选择
const showProductPicker = ref(false)
const products = ref<any[]>([])
const selectedProducts = computed(() => form.value.items)

// 加载商品列表
async function loadProducts() {
  try {
    const res: any = await getMaterials({ page_size: 100 })
    products.value = res.items.filter((p: any) => p.is_active)
  } catch (e) {
    console.error(e)
  }
}

// 添加商品
function addProduct(product: any) {
  if (selectedProducts.value.find(p => p.product_id === product.id)) {
    showToast('已添加该商品')
    return
  }
  form.value.items.push({
    product_id: product.id,
    product_name: product.name,
    quantity: 1,
    unit_price: product.price || 0
  })
  showProductPicker.value = false
}

// 删除商品
function removeProduct(index: number) {
  form.value.items.splice(index, 1)
}

// 更新商品数量
function updateQuantity(index: number, quantity: number) {
  if (quantity > 0) {
    form.value.items[index].quantity = quantity
  }
}

// 计算总价
const totalAmount = computed(() => {
  return form.value.items.reduce((sum, item) => {
    return sum + (item.quantity * item.unit_price)
  }, 0)
})

// 提交
async function handleSubmit() {
  if (!form.value.customer_address) {
    showToast('请填写客户地址（必填）')
    return
  }

  loading.value = true
  try {
    const data = {
      customer_name: form.value.customer_name || undefined,
      customer_address: form.value.customer_address || undefined,
      express_no: form.value.express_no || undefined,
      remark: form.value.remark || undefined,
      items: form.value.items.length > 0 ? form.value.items : undefined,
      order_date: form.value.order_date
    }
    await createSalesOrder(data)
    showToast('创建成功')
    router.back()
  } catch (e: any) {
    showToast(e.response?.data?.detail || e.message || '创建失败')
  } finally {
    loading.value = false
  }
}

loadProducts()
</script>

<template>
  <div class="create-page">
    <van-nav-bar title="创建销售订单" left-arrow @click-left="router.back()" />

    <van-form @submit="handleSubmit">
      <!-- 客户信息 -->
      <van-cell-group inset title="客户信息">
        <van-field v-model="form.customer_name" label="客户名称" placeholder="请输入（选填）" />
        <van-field v-model="form.customer_address" label="客户地址" placeholder="请输入（必填）" required />
      </van-cell-group>

      <!-- 快递信息 -->
      <van-cell-group inset title="快递信息">
        <van-field 
          v-model="form.express_no" 
          label="快递单号" 
          placeholder="请输入（选填）"
        />
      </van-cell-group>

      <!-- 商品列表 -->
      <van-cell-group inset title="商品列表">
        <div class="add-product" @click="showProductPicker = true">
          <van-icon name="plus" size="20" />
          <span>添加商品</span>
        </div>

        <div v-for="(item, index) in selectedProducts" :key="index" class="product-row">
          <div class="product-info">
            <div class="name">{{ item.product_name }}</div>
            <div class="price">¥{{ item.unit_price }}</div>
          </div>
          <div class="product-actions">
            <van-stepper 
              v-model="item.quantity" 
              :min="1"
              @change="(val: number) => updateQuantity(index, val)"
            />
            <van-icon name="cross" class="remove-btn" @click="removeProduct(index)" />
          </div>
        </div>

        <div v-if="selectedProducts.length > 0" class="total-row">
          <span>合计</span>
          <span class="total-price">¥{{ totalAmount }}</span>
        </div>
      </van-cell-group>

      <!-- 备注 -->
      <van-cell-group inset title="备注">
        <van-field v-model="form.remark" type="textarea" placeholder="请输入备注" rows="2" />
      </van-cell-group>

      <div class="submit-btn">
        <van-button type="primary" size="large" :loading="loading" native-type="submit">
          提交订单
        </van-button>
      </div>
    </van-form>

    <!-- 商品选择器 -->
    <van-popup v-model:show="showProductPicker" position="bottom" round>
      <van-picker
        title="选择商品"
        :columns="products.map(p => ({ text: p.name, value: p.id, ...p }))"
        @confirm="(cols: any) => {
          const p = products.find(x => x.id === cols[0].value)
          if (p) addProduct(p)
        }"
        @cancel="showProductPicker = false"
      />
    </van-popup>
  </div>
</template>

<style scoped>
.create-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 80px;
}

.add-product {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  color: #1989fa;
  border-bottom: 1px solid #f5f5f5;
}

.product-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f5f5f5;
}

.product-info .name {
  font-size: 14px;
  color: #333;
}

.product-info .price {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.product-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.remove-btn {
  color: #999;
}

.total-row {
  display: flex;
  justify-content: space-between;
  padding: 16px;
  font-size: 16px;
  font-weight: 600;
}

.total-price {
  color: #ff4d4f;
}

.submit-btn {
  padding: 16px;
}
</style>