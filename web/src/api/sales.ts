import request from '@/utils/request'
import type { SalesOrder, SalesOrderCreate } from '@/types/sales'

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

// 发布订单
export function publishSalesOrder(id: string) {
  return request.put<any>(`/sales-orders/${id}/publish`, {})
}

// 确认商品（发货用）
export function confirmSalesOrderItem(orderId: string, itemId: string) {
  return request.put<any>(`/sales-orders/${orderId}/items/${itemId}/confirm`, {})
}

// 确认快递单号
export function confirmExpress(orderId: string) {
  return request.put<any>(`/sales-orders/${orderId}/confirm-express`, {})
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