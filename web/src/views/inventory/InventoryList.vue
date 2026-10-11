<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showMessage } from '@/utils/request'
import request from '@/utils/request'
import { handleError } from '@/utils/request'
import { formatNumber } from '@/utils/number'
import HorizontalTable from '@/components/HorizontalTable.vue'

const router = useRouter()
const loading = ref(false)
const list = ref<any[]>([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })
const keyword = ref('')
const showLowStock = ref(false)

const categoryMap: Record<string, string> = {
  product: '产品',
  component: '部件'
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
    showMessage(errorMessage)
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
    <van-nav-bar title="库存管理" left-arrow @click-left="router.push('/materials')" />

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

    <!-- 库存表格 -->
    <div class="list-container">
      <van-pull-refresh v-model="loading" @refresh="fetchList">
        <HorizontalTable min-width="680px">
          <table class="inventory-table">
            <thead><tr><th>编码</th><th>名称</th><th>分类</th><th>当前库存</th><th>安全库存</th><th>单位</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="item in list" :key="item.material_id" @click="goDetail(item.material_id)">
                <td class="code-cell">{{ item.material_code }}</td>
                <td class="name-cell">{{ item.material_name }}</td>
                <td><span class="category-tag">{{ categoryMap[item.category] }}</span></td>
                <td :class="{ 'low-stock': item.current_stock < item.safety_stock }">{{ formatNumber(item.current_stock) }}</td>
                <td>{{ formatNumber(item.safety_stock) }}</td>
                <td>{{ item.unit }}</td>
                <td><span v-if="item.current_stock < item.safety_stock" class="low-stock-tag">库存不足</span><span v-else class="normal-stock-tag">正常</span></td>
              </tr>
            </tbody>
          </table>
          <van-empty v-if="!loading && list.length === 0" description="暂无库存" />
        </HorizontalTable>
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

.inventory-table { width: 100%; border-collapse: collapse; font-size: 13px; white-space: nowrap; }
.inventory-table thead { background: #fafafa; }
.inventory-table th { padding: 12px 10px; text-align: left; color: #666; font-weight: 600; border-bottom: 2px solid #ddd; }
.inventory-table td { padding: 14px 10px; color: #333; border-bottom: 1px solid #ebebeb; }
.inventory-table tbody tr { cursor: pointer; }
.inventory-table tbody tr:hover { background: #f8f9ff; }
.inventory-table tbody tr:last-child td { border-bottom: none; }
.code-cell { color: #777; font-family: monospace; }
.name-cell { font-weight: 600; }
.category-tag { color: #1989fa; background: #e6f7ff; padding: 3px 9px; border-radius: 4px; }
.low-stock { color: #ff4d4f !important; font-weight: 600; }

.low-stock-tag {
  display: inline-block;
  font-size: 12px;
  color: #ff4d4f;
  background: #fff1f0;
  padding: 3px 9px;
  border-radius: 4px;
}

.normal-stock-tag { display: inline-block; font-size: 12px; color: #07c160; background: #f0fff5; padding: 3px 9px; border-radius: 4px; }
</style>
