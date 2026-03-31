import type { ID, DateTime, DateType } from './common'

// 销售订单状态
export type SalesOrderStatus = 'draft' | 'published' | 'in_progress' | 'completed' | 'cancelled'

// 销售订单
export interface SalesOrder {
  id: ID
  order_no: string
  customer_id?: ID
  customer_name?: string
  customer_address?: string
  express_no?: string
  status: SalesOrderStatus
  total_amount: number
  remark?: string
  items: SalesOrderItem[]
  created_at: DateTime
  updated_at: DateTime
}

// 销售订单明细
export interface SalesOrderItem {
  id: ID
  product_id: ID
  product_name?: string
  quantity: number
  unit_price: number
  amount: number
  is_confirmed: boolean
  created_at: DateTime
  product?: any
}

// 创建销售订单
export interface SalesOrderCreate {
  customer_name?: string
  customer_address?: string
  express_no?: string
  remark?: string
  items?: {
    product_id: ID
    quantity: number
    unit_price: number
  }[]
}

// 更新销售订单
export interface SalesOrderUpdate {
  customer_name?: string
  customer_address?: string
  express_no?: string
  remark?: string
}