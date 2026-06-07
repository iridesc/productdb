import request from '@/utils/request'
import type { SalesOrder, SalesOrderCreate, SalesOrderImage, SalesOrderImageType } from '@/types/sales'

// 销售订单列表
export function getSalesOrders(params: {
  page?: number
  page_size?: number
  status?: string
}) {
  return request.get<{ total: number; items: SalesOrder[] }>('/sales-orders', { params })
}

// 销售订单详情
export function getSalesOrder(id: string) {
  return request.get<SalesOrder>(`/sales-orders/${id}`)
}

// 创建销售订单
export function createSalesOrder(data: SalesOrderCreate) {
  return request.post<SalesOrder>('/sales-orders', data)
}

// 更新销售订单
export function updateSalesOrder(id: string, data: any) {
  return request.put<SalesOrder>(`/sales-orders/${id}`, data)
}

// 更新销售订单商品
export function updateSalesOrderItems(id: string, items: any[]) {
  return request.put<SalesOrder>(`/sales-orders/${id}/items`, items)
}

// 发布订单
export function publishSalesOrder(id: string) {
  return request.put<any>(`/sales-orders/${id}/publish`, {})
}

// 确认商品（发货用）
export function confirmSalesOrderItem(orderId: string, itemId: string) {
  return request.put<any>(`/sales-orders/${orderId}/items/${itemId}/confirm`, {})
}

// 完成订单
export function completeSalesOrder(id: string) {
  return request.put<any>(`/sales-orders/${id}/complete`, {})
}

// 取消订单
export function cancelSalesOrder(id: string) {
  return request.put<any>(`/sales-orders/${id}/cancel`, {})
}

// 删除订单
export function deleteSalesOrder(id: string) {
  return request.delete(`/sales-orders/${id}`)
}

// 上传销售订单凭证图片
export function uploadSalesOrderImage(orderId: string, file: File, imageType: SalesOrderImageType) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('image_type', imageType)

  return request.post<SalesOrderImage>(`/sales-orders/${orderId}/images`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 30000,
  })
}

// 获取销售订单凭证图片
export function getSalesOrderImages(orderId: string) {
  return request.get<SalesOrderImage[]>(`/sales-orders/${orderId}/images`)
}

// 删除销售订单凭证图片
export function deleteSalesOrderImage(imageId: string) {
  return request.delete(`/sales-orders/images/${imageId}`)
}