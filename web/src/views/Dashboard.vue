<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/store/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

const active = ref(0)

// 快速入口
const quickActions = [
  { name: '创建销售订单', path: '/sales-orders/create', icon: 'orders-o' },
  { name: '创建生产订单', path: '/production-orders/create', icon: 'friends-o' },
  { name: '物料管理', path: '/materials', icon: 'bag-o' },
  { name: '库存查询', path: '/inventory', icon: 'search' }
]

// 快捷导航
function navigate(path: string) {
  router.push(path)
}

function handleLogout() {
  userStore.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="dashboard">
    <van-tabbar v-model="active" @change="(idx) => active = idx">
      <van-tabbar-item icon="home-o" to="/dashboard">首页</van-tabbar-item>
      <van-tabbar-item icon="orders-o" to="/sales-orders">销售</van-tabbar-item>
      <van-tabbar-item icon="friends-o" to="/production-orders">生产</van-tabbar-item>
      <van-tabbar-item icon="bag-o" to="/materials">物料</van-tabbar-item>
      <van-tabbar-item icon="setting-o" to="/settings">设置</van-tabbar-item>
    </van-tabbar>

    <div class="page-content">
      <div class="header">
        <div class="title">欢迎使用 ERP 系统</div>
        <div class="logout" @click="handleLogout">退出</div>
      </div>

      <!-- 快捷入口 -->
      <div class="card">
        <div class="card-title">快捷操作</div>
        <van-grid :column-num="4" :gutter="10">
          <van-grid-item 
            v-for="item in quickActions" 
            :key="item.path"
            :icon="item.icon" 
            :text="item.name"
            @click="navigate(item.path)"
          />
        </van-grid>
      </div>

      <!-- 功能说明 -->
      <div class="card">
        <div class="card-title">功能模块</div>
        <div class="module-list">
          <div class="module-item" @click="navigate('/sales-orders')">
            <van-icon name="orders-o" size="24" color="#1989fa" />
            <div class="module-info">
              <div class="module-name">销售订单</div>
              <div class="module-desc">管理销售订单和发货</div>
            </div>
            <van-icon name="arrow" size="16" color="#999" />
          </div>
          <div class="module-item" @click="navigate('/production-orders')">
            <van-icon name="friends-o" size="24" color="#07c160" />
            <div class="module-info">
              <div class="module-name">生产订单</div>
              <div class="module-desc">管理生产计划和物料</div>
            </div>
            <van-icon name="arrow" size="16" color="#999" />
          </div>
          <div class="module-item" @click="navigate('/materials')">
            <van-icon name="bag-o" size="24" color="#ff976a" />
            <div class="module-info">
              <div class="module-name">物料管理</div>
              <div class="module-desc">管理产品和物料信息</div>
            </div>
            <van-icon name="arrow" size="16" color="#999" />
          </div>
          <div class="module-item" @click="navigate('/inventory')">
            <van-icon name="search" size="24" color="#7232dd" />
            <div class="module-info">
              <div class="module-name">库存管理</div>
              <div class="module-desc">查看实时库存和流水</div>
            </div>
            <van-icon name="arrow" size="16" color="#999" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100vh;
  padding-bottom: 50px;
}

.page-content {
  padding: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.logout {
  font-size: 14px;
  color: #999;
}

.module-list {
  display: flex;
  flex-direction: column;
}

.module-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
}

.module-item:last-child {
  border-bottom: none;
}

.module-info {
  flex: 1;
  margin-left: 12px;
}

.module-name {
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.module-desc {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>