<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showLoadingToast, Empty } from 'vant'
import { getMaterials, deleteMaterial } from '@/api/material'
import type { Material } from '@/types/material'

const router = useRouter()
const loading = ref(false)
const list = ref<Material[]>([])
const pagination = ref({ page: 1, page_size: 20, total: 0 })
const keyword = ref('')

const statusMap: Record<string, string> = {
  finished_product: '成品',
  semi_finished: '半成品',
  raw_material: '原材料',
  auxiliary: '辅料'
}

async function fetchList() {
  loading.value = true
  try {
    const res: any = await getMaterials({
      page: pagination.value.page,
      page_size: pagination.value.page_size,
      keyword: keyword.value || undefined
    })
    list.value = res.items
    pagination.value.total = res.total
  } catch (e: any) {
    showToast(e.message || '加载失败')
  } finally {
    loading.value = false
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
    <van-nav-bar title="物料管理" left-arrow @click-left="router.back()" />

    <!-- 搜索 -->
    <div class="search-bar">
      <van-search
        v-model="keyword"
        placeholder="搜索物料名称/编码"
        @search="handleSearch"
        shape="round"
      />
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

    <!-- 新增按钮 -->
    <van-button
      type="primary"
      size="large"
      block
      class="add-btn"
      @click="goCreate"
    >
      新增物料
    </van-button>
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

.add-btn {
  position: fixed;
  bottom: 20px;
  left: 16px;
  right: 16px;
  z-index: 100;
}
</style>