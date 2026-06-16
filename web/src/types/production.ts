import type { ID, DateTime } from './common'

// 生产订单状态
export type ProductionOrderStatus = 'pending' | 'in_production' | 'completed' | 'cancelled'

// 生产订单产品图
export interface ProductionOrderImage {
  id: ID
  order_id: ID
  image_type: string
  image_url: string
  sort_order: number
  created_at: DateTime
}

// 生产订单
export interface ProductionOrder {
  id: ID
  order_no: string
  product_id: ID
  product_name: string
  quantity: number
  completed_quantity: number
  status: ProductionOrderStatus
  remark?: string
  items: ProductionOrderItem[]
  images: ProductionOrderImage[]
  created_at: DateTime
  updated_at: DateTime
  product?: {
    id: ID
    name: string
    code: string
    thumbnail_url?: string
  }
}

// 生产订单明细
export interface ProductionOrderItem {
  id: ID
  material_id: ID
  material_name: string
  quantity: number
  consumed_quantity: number
  is_distributed: boolean
  created_at: DateTime
  material?: {
    id: ID
    name: string
    thumbnail_url?: string
  }
}

// 创建生产订单
export interface ProductionOrderCreate {
  product_id: ID
  quantity: number
  remark?: string
}

// 更新生产订单（仅草稿状态）
export interface ProductionOrderUpdate {
  product_id?: ID
  quantity?: number
  remark?: string
}
