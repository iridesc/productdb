<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, Empty } from 'vant'
import { getMaterials, deleteMaterial } from '@/api/material'
import type { Material } from '@/types/material'
import { handleError } from '@/utils/request'

const router = useRouter()
const loading = ref(false)
const list = ref<Material[]>([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })
const keyword = ref('')
const selectedCategory = ref<string>('')

const statusMap: Record<string, string> = {
  finished_product: '成品',
  semi_finished: '半成品',
  raw_material: '原材料',
  auxiliary: '辅料'
}

const categoryOptions = [
  { text: '全部', value: '' },
  { text: '成品', value: 'finished_product' },
  { text: '半成品', value: 'semi_finished' },
  { text: '原材料', value: 'raw_material' },
  { text: '辅料', value: 'auxiliary' }
]

async function fetchList() {
  loading.value = true
  try {
    const res: any = await getMaterials({
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      keyword: keyword.value || undefined,
      category: selectedCategory.value || undefined
    })
    list.value = res.items
    pagination.value.total = res.total
  } catch (e) {
    const errorMessage = handleError(e)
    showToast(errorMessage)
  } finally {
    loading.value = false
  }
}

function openCategoryFilter() {
  // 使用原生的prompt作为临时解决方案
  const categories = categoryOptions.map((opt, index) => `${index + 1}. ${opt.text}`).join('\n')
  const input = prompt(`请选择分类:\n${categories}\n\n请输入编号:`, '1')
  
  if (input) {
    const index = parseInt(input) - 1
    if (index >= 0 && index < categoryOptions.length) {
      selectedCategory.value = categoryOptions[index].value
      pagination.value.page = 1
      fetchList()
    }
  }
}

function handleSearch() {
  pagination.value.page = 1
  fetchList()
}

function goCreate() {
  router.push('/materials/create')
}

function goDetail(id: string) {
  router.push(`/materials/${id}`)
}

onMounted(() => {
  fetchList()
})
</script>

<template>
  <div class="materials-page">
    <van-nav-bar 
      title="物料管理" 
      left-arrow 
      @click-left="router.back()"
    >
      <template #right>
        <van-icon name="plus" size="18" @click="goCreate" />
      </template>
    </van-nav-bar>

    <!-- 搜索和筛选 -->
    <div class="search-bar">
      <div class="search-row">
        <van-search
          v-model="keyword"
          placeholder="搜索物料名称/编码"
          @search="handleSearch"
          shape="round"
          style="flex: 1; margin-right: 12px;"
        />
        <van-button
          type="default"
          @click="openCategoryFilter"
          style="white-space: nowrap;"
        >
          {{ selectedCategory ? statusMap[selectedCategory] : '分类筛选' }}
        </van-button>
      </div>
    </div>

    <!-- 列表 -->
    <div class="list-container">
      <van-pull-refresh v-model="loading" @refresh="fetchList">
        <van-list
          :loading="loading"
          :finished="!loading && list.length >= pagination.total"
          @load="fetchList"
        >
          <div 
            v-for="item in list" 
            :key="item.id" 
            class="list-item"
            @click="goDetail(item.id)"
          >
            <div class="item-info">
              <div class="item-name">{{ item.name }}</div>
              <div class="item-meta">
                <span class="item-code">{{ item.code }}</span>
                <span class="item-category">{{ statusMap[item.category] || item.category }}</span>
              </div>
            </div>
            <div class="item-stock">
              <div class="stock-num" :class="{ 'low-stock': item.current_stock < item.safety_stock }">
                {{ item.current_stock }} {{ item.unit }}
              </div>
              <div class="stock-label">库存</div>
            </div>
          </div>

          <van-empty v-if="!loading && list.length === 0" description="暂无物料" />
        </van-list>
      </van-pull-refresh>
    </div>
  </div>
</template>

<style scoped>
.materials-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.search-bar {
  background: #fff;
  padding: 12px 16px;
}

.search-row {
  display: flex;
  align-items: center;
}

.list-container {
  padding: 0 16px;
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


</style>