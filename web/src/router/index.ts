import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '首页', requiresAuth: true }
  },
  {
    path: '/materials',
    name: 'Materials',
    component: () => import('@/views/materials/MaterialList.vue'),
    meta: { title: '物料管理', requiresAuth: true }
  },
  {
    path: '/materials/create',
    name: 'MaterialCreate',
    component: () => import('@/views/materials/MaterialCreate.vue'),
    meta: { title: '创建物料', requiresAuth: true }
  },
  {
    path: '/materials/:id',
    name: 'MaterialDetail',
    component: () => import('@/views/materials/MaterialDetail.vue'),
    meta: { title: '物料详情', requiresAuth: true }
  },
  {
    path: '/sales-orders',
    name: 'SalesOrders',
    component: () => import('@/views/sales/SalesOrderList.vue'),
    meta: { title: '销售订单', requiresAuth: true }
  },
  {
    path: '/sales-orders/create',
    name: 'SalesOrderCreate',
    component: () => import('@/views/sales/SalesOrderCreate.vue'),
    meta: { title: '创建销售订单', requiresAuth: true }
  },
  {
    path: '/sales-orders/:id',
    name: 'SalesOrderDetail',
    component: () => import('@/views/sales/SalesOrderDetail.vue'),
    meta: { title: '销售订单详情', requiresAuth: true }
  },
  {
    path: '/production-orders',
    name: 'ProductionOrders',
    component: () => import('@/views/production/ProductionOrderList.vue'),
    meta: { title: '生产订单', requiresAuth: true }
  },
  {
    path: '/production-orders/create',
    name: 'ProductionOrderCreate',
    component: () => import('@/views/production/ProductionOrderCreate.vue'),
    meta: { title: '创建生产订单', requiresAuth: true }
  },
  {
    path: '/production-orders/:id',
    name: 'ProductionOrderDetail',
    component: () => import('@/views/production/ProductionOrderDetail.vue'),
    meta: { title: '生产订单详情', requiresAuth: true }
  },
  {
    path: '/inventory',
    name: 'Inventory',
    component: () => import('@/views/inventory/InventoryList.vue'),
    meta: { title: '库存管理', requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title as string
  }
  next()
})

export default router