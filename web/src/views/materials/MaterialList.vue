<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { previewImage } from '@/utils/image'
import { Empty } from 'vant'
import { showMessage } from '@/utils/request'
import { getMaterials, deleteMaterial } from '@/api/material'
import type { Material } from '@/types/material'
import { handleError } from '@/utils/request'
import { formatNumber } from '@/utils/number'

const router = useRouter()
const loading = ref(false)
const list = ref<Material[]>([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })
const keyword = ref('')
const selectedCategory = ref<string[]>([])
const showCategoryPopup = ref(false)
const sortBy = ref('')
const sortOrder = ref<'asc' | 'desc'>('asc')

const statusMap: Record<string, string> = {
  product: '产品',
  component: '部件'
}

const categoryColor: Record<string, string> = {
  product: '#1890ff',
  component: '#fa8c16'
}

const categoryOptions = [
  { text: '全部', value: '' },
  { text: '产品', value: 'product' },
  { text: '部件', value: 'component' }
]

async function fetchList() {
  loading.value = true
  try {
    const res: any = await getMaterials({
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      keyword: keyword.value || undefined,
      category: selectedCategory.value.length > 0 ? selectedCategory.value.join(',') : undefined,
      sort_by: sortBy.value || undefined,
      sort_order: sortOrder.value || undefined
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
  showCategoryPopup.value = true
}

function handleCategoryClick(option: { text: string; value: string }) {
  if (option.value === '') {
    // 全部选项：选所有非"全部"的选项，或者清空
    if (selectedCategory.value.length === categoryOptions.length - 1) {
      selectedCategory.value = []
    } else {
      selectedCategory.value = categoryOptions.filter(o => o.value !== '').map(o => o.value)
    }
  } else {
    const index = selectedCategory.value.indexOf(option.value)
    if (index > -1) {
      selectedCategory.value.splice(index, 1)
    } else {
      selectedCategory.value.push(option.value)
    }
  }
}

function confirmCategoryFilter() {
  showCategoryPopup.value = false
  pagination.value.page = 1
  fetchList()
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

function toggleSort(field: string) {
  if (sortBy.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = field
    sortOrder.value = 'asc'
  }
  pagination.value.page = 1
  fetchList()
}

function sortIndicator(field: string): string {
  if (sortBy.value !== field) return ''
  return sortOrder.value === 'asc' ? ' ↑' : ' ↓'
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
          {{ selectedCategory.length > 0 ? `已选${selectedCategory.length}个` : '分类筛选' }}
        </van-button>
      </div>
    </div>

    <!-- 分类筛选弹窗 -->
    <van-popup v-model:show="showCategoryPopup" position="bottom" round>
      <div class="category-popup">
        <div class="popup-header">
          <span class="popup-title">选择分类</span>
          <van-button type="primary" size="small" @click="confirmCategoryFilter">确定</van-button>
        </div>
        <van-checkbox-group v-model="selectedCategory">
          <van-cell-group>
            <van-cell
              v-for="option in categoryOptions"
              :key="option.value"
              clickable
              @click="handleCategoryClick(option)"
            >
              <template #title>
                <span class="category-text">{{ option.text }}</span>
              </template>
              <template #right-icon>
                <van-checkbox :name="option.value" @click.stop />
              </template>
            </van-cell>
          </van-cell-group>
        </van-checkbox-group>
      </div>
    </van-popup>

    <!-- 表格 -->
    <div class="table-container">
      <van-pull-refresh v-model="loading" @refresh="fetchList">
        <div class="table-wrapper">
          <table class="material-table">
            <thead>
              <tr>
                <th class="sortable" @click="toggleSort('code')">编码{{ sortIndicator('code') }}</th>
                <th class="thumb-cell">图片</th>
                <th class="sortable" @click="toggleSort('name')">名称{{ sortIndicator('name') }}</th>
                <th class="sortable" @click="toggleSort('category')">分类{{ sortIndicator('category') }}</th>
                <th class="sortable" @click="toggleSort('current_stock')">库存{{ sortIndicator('current_stock') }}</th>
                <th class="sortable" @click="toggleSort('safety_stock')">安全库存{{ sortIndicator('safety_stock') }}</th>
                <th class="sortable" @click="toggleSort('unit')">单位{{ sortIndicator('unit') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in list" :key="item.id" @click="goDetail(item.id)">
                <td class="code-cell">{{ item.code }}</td>
                <td class="thumb-cell">
                  <img
                    v-if="item.thumbnail_url"
                    class="material-thumb"
                    :src="item.thumbnail_url"
                    :alt="item.name"
                    @click.stop="previewImage(item.thumbnail_url)"
                  />
                  <div v-else class="material-thumb material-thumb-placeholder">
                    <van-icon name="photo-o" size="16" />
                  </div>
                </td>
                <td class="name-cell">{{ item.name }}</td>
                <td>
                  <span class="category-tag"
                    :style="{ background: categoryColor[item.category] + '20', color: categoryColor[item.category] }">
                    {{ statusMap[item.category] || item.category }}
                  </span>
                </td>
                <td :class="{ 'low-stock': item.current_stock < item.safety_stock }">
                  {{ formatNumber(item.current_stock) }}
                </td>
                <td>{{ formatNumber(item.safety_stock) }}</td>
                <td class="center-cell">{{ item.unit }}</td>
              </tr>
            </tbody>
          </table>

          <van-empty v-if="!loading && list.length === 0" description="暂无物料" />
        </div>
      </van-pull-refresh>
      <van-pagination
        v-if="pagination.total > pagination.page_size"
        v-model="pagination.page"
        :total-items="pagination.total"
        :items-per-page="pagination.page_size"
        @change="fetchList"
      />
      <div v-if="pagination.total > pagination.page_size" style="text-align:center;color:#999;font-size:12px;padding:8px">
        共 {{ pagination.total }} 条
      </div>
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
}

.material-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.material-table thead {
  background: #fafafa;
}

.material-table th {
  padding: 12px 8px;
  text-align: left;
  font-weight: 600;
  color: #666;
  border-bottom: 2px solid #ddd;
  font-size: 13px;
  white-space: nowrap;
}

.material-table th.sortable {
  cursor: pointer;
  user-select: none;
  transition: color 0.15s;
}

.material-table th.sortable:hover {
  color: #1989fa;
}

.material-table td {
  padding: 12px 8px;
  border-bottom: 1px solid #ebebeb;
  color: #333;
  vertical-align: middle;
  white-space: nowrap;
}

.material-table tbody tr {
  cursor: pointer;
  transition: background-color 0.2s;
}

.material-table tbody tr:hover {
  background: #f8f9ff;
}

.material-table tbody tr:hover td {
  color: #1a1a1a;
}

.material-table tbody tr:hover .code-cell {
  color: #555;
}

.material-table tbody tr:last-child td {
  border-bottom: none;
}

.thumb-cell {
  width: 56px;
  text-align: left;
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
  text-align: left;
}

.category-tag {
  display: inline-block;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 4px;
}

.category-popup {
  padding: 16px;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.popup-title {
  font-size: 16px;
  font-weight: 600;
}

.category-text {
  margin-left: 8px;
}
</style>
