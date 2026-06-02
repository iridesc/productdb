import request from '@/utils/request'
import type { ProductionOrder, ProductionOrderCreate } from '@/types/production'

// 生产订单列表
export function getProductionOrders(params: {
  page?: number
  page_size?: number
  status?: string
  product_id?: string
}) {
  return request.get<{ total: number; items: ProductionOrder[] }>('/production-orders', { params })
}

// 生产订单详情
export function getProductionOrder(id: string) {
  return request.get<ProductionOrder>(`/production-orders/${id}`)
}

// 创建生产订单（草稿）
export function createProductionOrder(data: ProductionOrderCreate) {
  return request.post<ProductionOrder>('/production-orders', data)
}

// 更新生产订单（草稿可编辑）
export function updateProductionOrder(id: string, data: any) {
  return request.put<ProductionOrder>(`/production-orders/${id}`, data)
}

// 发布生产订单（草稿 → 待生产，校验库存并扣减）
export function publishProductionOrder(id: string) {
  return request.put<any>(`/production-orders/${id}/publish`, {})
}

// 开工（待生产 → 生产中）
export function startProductionOrder(id: string) {
  return request.put<any>(`/production-orders/${id}/start`, {})
}

// 报工完成（生产中 → 已完成，成品入库）
export function completeProductionOrder(id: string) {
  return request.put<any>(`/production-orders/${id}/complete`, {})
}

// 取消生产订单（退回库存）
export function cancelProductionOrder(id: string) {
  return request.put<any>(`/production-orders/${id}/cancel`, {})
}

// 删除生产订单（仅草稿）
export function deleteProductionOrder(id: string) {
  return request.delete(`/production-orders/${id}`)
}

// 获取物料需求列表
export function getProductionMaterials(orderId: string) {
  return request.get<any[]>(`/production-orders/${orderId}/materials`)
}

// 获取当前用户角色
export function getCurrentUserRoles() {
  return request.get<{ user_id: string; username: string; roles: { code: string; name: string }[] }>('/auth/me/roles')
}