import type { ID, DateTime } from './common'

// 物料分类
export type MaterialCategory = 'finished_product' | 'semi_finished' | 'raw_material' | 'auxiliary'

// 物料
export interface Material {
  id: ID
  code: string
  name: string
  category: MaterialCategory
  unit: string
  specification?: string
  safety_stock: number
  current_stock: number
  price: number
  sale_price: number
  other_cost: number
  bom_cost: number
  total_cost: number
  description?: string
  is_active: boolean
  tags?: Tag[]
  images?: MaterialImage[]
  created_at: DateTime
  updated_at: DateTime
}

export interface MaterialCreate {
  code: string
  name: string
  category: MaterialCategory
  unit: string
  safety_stock?: number
  price?: number
  sale_price?: number
  other_cost?: number
  description?: string
}

export interface MaterialUpdate {
  name?: string
  category?: MaterialCategory
  unit?: string
  specification?: string
  safety_stock?: number
  current_stock?: number
  price?: number
  sale_price?: number
  other_cost?: number
  description?: string
  is_active?: boolean
}

// 标签
export interface Tag {
  id: ID
  name: string
  color?: string
}

// 物料图片
export interface MaterialImage {
  id: ID
  material_id: ID
  image_url: string
  sort_order: number
  created_at: DateTime
}