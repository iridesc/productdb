import request from '@/utils/request'
import type { ProductionOrder, ProductionOrderCreate } from '@/types/production'

// 生产订单列表
export function getProductionOrders(params: {
  page?: number
  page_size?: number
  status?: string
}) {
  return request.get<{ total: number; items: ProductionOrder[] }>('/production-orders', { params })
}

// 生产订单详情
export function getProductionOrder(id: string) {
  return request.get<ProductionOrder>(`/production-orders/${id}`)
}

// 创建生产订单
export function createProductionOrder(data: ProductionOrderCreate) {
  return request.post<ProductionOrder>('/production-orders', data)
}

// 发布生产订单
export function publishProductionOrder(id: string) {
  return request.put<any>(`/production-orders/${id}/publish`, {})
}

// 分配物料库存
export function distributeProductionItem(orderId: string, itemId: string) {
  return request.put<any>(`/production-orders/${orderId}/items/${itemId}/distribute`, {})
}

// 完成生产订单
export function completeProductionOrder(id: string) {
  return request.put<any>(`/production-orders/${id}/complete`, {})
}

// 取消生产订单
export function cancelProductionOrder(id: string) {
  return request.put<any>(`/production-orders/${id}/cancel`, {})
}

// 删除生产订单
export function deleteProductionOrder(id: string) {
  return request.delete(`/production-orders/${id}`)
}