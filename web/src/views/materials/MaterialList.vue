<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Empty } from 'vant'
import { showMessage } from '@/utils/request'
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

const categoryColor: Record<string, string> = {
  finished_product: '#52c41a',
  semi_finished: '#fa8c16',
  raw_material: '#1890ff',
  auxiliary: '#722ed1'
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
    showMessage(errorMessage)
  } finally {
    loading.value = false
  }
}

function openCategoryFilter() {
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

    <!-- 表格 -->
    <div class="table-container">
      <van-pull-refresh v-model="loading" @refresh="fetchList">
        <div class="table-wrapper">
          <table class="material-table">
            <thead>
              <tr>
                <th class="thumb-cell">图片</th>
                <th>物料名称</th>
                <th>物料编码</th>
                <th>分类</th>
                <th>当前库存</th>
                <th>安全库存</th>
                <th>单位</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in list" :key="item.id" @click="goDetail(item.id)">
                <td class="thumb-cell">
                  <img
                    v-if="item.thumbnail_url"
                    class="material-thumb"
                    :src="item.thumbnail_url"
                    :alt="item.name"
                  />
                  <div v-else class="material-thumb material-thumb-placeholder">
                    <van-icon name="photo-o" size="16" />
                  </div>
                </td>
                <td class="name-cell">{{ item.name }}</td>
                <td class="code-cell">{{ item.code }}</td>
                <td>
                  <span class="category-tag"
                    :style="{ background: categoryColor[item.category] + '20', color: categoryColor[item.category] }">
                    {{ statusMap[item.category] || item.category }}
                  </span>
                </td>
                <td :class="{ 'low-stock': item.current_stock < item.safety_stock }">
                  {{ item.current_stock }}
                </td>
                <td>{{ item.safety_stock }}</td>
                <td class="center-cell">{{ item.unit }}</td>
              </tr>
            </tbody>
          </table>

          <van-empty v-if="!loading && list.length === 0" description="暂无物料" />
        </div>
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

.table-container {
  padding: 16px;
}

.table-wrapper {
  background: #fff;
  border-radius: 8px;
  overflow-x: auto;
}

.material-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  white-space: nowrap;
}

.material-table thead {
  background: #fafafa;
}

.material-table th {
  padding: 12px 10px;
  text-align: left;
  font-weight: 600;
  color: #666;
  border-bottom: 2px solid #eee;
  font-size: 13px;
}

.material-table td {
  padding: 14px 10px;
  border-bottom: 1px solid #f5f5f5;
  color: #333;
  vertical-align: middle;
}

.material-table tbody tr {
  cursor: pointer;
  transition: background-color 0.2s;
}

.material-table tbody tr:hover {
  background: #f8f9ff;
}

.material-table tbody tr:last-child td {
  border-bottom: none;
}

.thumb-cell {
  width: 56px;
  text-align: center;
}

.material-thumb {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  object-fit: cover;
  display: block;
  margin: 0 auto;
  background: #f5f5f5;
}

.material-thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ccc;
}

.name-cell {
  font-weight: 600;
  color: #333;
}

.code-cell {
  color: #999;
  font-family: monospace;
}

.low-stock {
  color: #ff4d4f;
  font-weight: 600;
}

.center-cell {
  text-align: center;
}

.category-tag {
  display: inline-block;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 4px;
}
</style>
