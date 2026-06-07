import request from '@/utils/request'
import type { ProductionOrder, ProductionOrderCreate, ProductionOrderImage } from '@/types/production'

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

// 创建生产订单
export function createProductionOrder(data: ProductionOrderCreate) {
  return request.post<ProductionOrder>('/production-orders', data)
}

// 发布生产订单
export function publishProductionOrder(id: string) {
  return request.put<any>(`/production-orders/${id}/publish`, {})
}

// 检查物料（标记已消耗）
export function distributeProductionItem(orderId: string, itemId: string) {
  return request.put<any>(`/production-orders/${orderId}/items/${itemId}/distribute`, {})
}

// 确认产出数量
export function setProductionYield(orderId: string, completedQuantity: number) {
  return request.put<any>(`/production-orders/${orderId}/yield`, { completed_quantity: completedQuantity })
}

// 上传产品图
export function uploadProductionOrderImage(orderId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<ProductionOrderImage>(`/production-orders/${orderId}/images`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000,
  })
}

// 获取产品图列表
export function getProductionOrderImages(orderId: string) {
  return request.get<ProductionOrderImage[]>(`/production-orders/${orderId}/images`)
}

// 删除产品图
export function deleteProductionOrderImage(imageId: string) {
  return request.delete(`/production-orders/images/${imageId}`)
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
