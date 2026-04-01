<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import request from '@/utils/request'
import { handleError } from '@/utils/request'

const router = useRouter()
const loading = ref(false)
const list = ref<any[]>([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })
const keyword = ref('')
const showLowStock = ref(false)

const categoryMap: Record<string, string> = {
  finished_product: '成品',
  semi_finished: '半成品',
  raw_material: '原材料',
  auxiliary: '辅料'
}

async function fetchList() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.value.page,
      page_size: pagination.value.page_size
    }
    if (keyword.value) params.keyword = keyword.value
    if (showLowStock.value) params.low_stock = true
    
    const res: any = await request.get('/inventory', { params })
    list.value = res.items
    pagination.value.total = res.total
  } catch (e) {
    const errorMessage = handleError(e)
    showToast(errorMessage)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.value.page = 1
  fetchList()
}

function goDetail(id: string) {
  router.push(`/materials/${id}`)
}

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="inventory-page">
    <van-nav-bar title="库存管理" left-arrow @click-left="router.back()" />

    <!-- 搜索 -->
    <div class="search-bar">
      <van-search
        v-model="keyword"
        placeholder="搜索物料"
        @search="handleSearch"
        shape="round"
      />
      <van-checkbox v-model="showLowStock" @change="handleSearch" class="low-stock-checkbox">
        低库存预警
      </van-checkbox>
    </div>

    <!-- 列表 -->
    <div class="list-container">
      <van-pull-refresh v-model="loading" @refresh="fetchList">
        <div 
          v-for="item in list" 
          :key="item.material_id" 
          class="list-item"
          @click="goDetail(item.material_id)"
        >
          <div class="item-info">
            <div class="item-name">{{ item.material_name }}</div>
            <div class="item-meta">
              <span class="item-code">{{ item.material_code }}</span>
              <span class="item-category">{{ categoryMap[item.category] }}</span>
            </div>
          </div>
          <div class="item-stock">
            <div class="stock-num" :class="{ 'low-stock': item.current_stock < item.safety_stock }">
              {{ item.current_stock }} {{ item.unit }}
            </div>
            <div class="stock-label">库存</div>
            <div v-if="item.current_stock < item.safety_stock" class="low-stock-tag">
              低于安全库存 {{ item.safety_stock }}
            </div>
          </div>
        </div>

        <van-empty v-if="!loading && list.length === 0" description="暂无库存" />
      </van-pull-refresh>
    </div>
  </div>
</template>

<style scoped>
.inventory-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.search-bar {
  background: #fff;
  padding: 12px 16px;
}

.low-stock-checkbox {
  margin-top: 8px;
}

.list-container {
  padding: 16px;
}

.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.item-info {
  flex: 1;
}

.item-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 6px;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-code {
  font-size: 12px;
  color: #999;
}

.item-category {
  font-size: 12px;
  color: #1989fa;
  background: #e6f7ff;
  padding: 2px 8px;
  border-radius: 4px;
}

.item-stock {
  text-align: right;
}

.stock-num {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.stock-num.low-stock {
  color: #ff4d4f;
}

.stock-label {
  font-size: 12px;
  color: #999;
}

.low-stock-tag {
  font-size: 12px;
  color: #ff4d4f;
  margin-top: 4px;
}
</style>