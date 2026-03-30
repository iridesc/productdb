import type { ID, DateTime } from './common'

// 生产订单状态
export type ProductionOrderStatus = 'draft' | 'published' | 'in_progress' | 'completed' | 'cancelled'

// 生产订单
export interface ProductionOrder {
  id: ID
  order_no: string
  product_id: ID
  product_name: string
  quantity: number
  status: ProductionOrderStatus
  remark?: string
  items: ProductionOrderItem[]
  created_at: DateTime
  updated_at: DateTime
}

// 生产订单明细
export interface ProductionOrderItem {
  id: ID
  material_id: ID
  material_name: string
  quantity: number
  is_distributed: boolean
  created_at: DateTime
}

// 创建生产订单
export interface ProductionOrderCreate {
  product_id: ID
  quantity: number
  remark?: string
}