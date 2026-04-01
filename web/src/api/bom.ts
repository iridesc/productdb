import request from '@/utils/request'
import type { ID } from '@/types/common'

export interface BOMItem {
  id: ID
  product_id: ID
  product_name: string
  product_code: string
  material_id: ID
  material_name: string
  material_code: string
  quantity: number
  scrap_rate: number
  is_optional: boolean
  note?: string
}

export interface BOMCreate {
  product_id: string
  material_id: string
  quantity: number
  scrap_rate?: number
  is_optional?: boolean
  note?: string
}

export function getProductBOM(productId: string) {
  return request.get<BOMItem[]>(`/boms/product/${productId}`)
}

export function createBOM(data: BOMCreate) {
  return request.post<BOMItem>('/boms', data)
}

export function deleteBOM(bomId: string) {
  return request.delete(`/boms/${bomId}`)
}

export function updateBOM(bomId: string, data: Partial<BOMCreate>) {
  return request.put<BOMItem>(`/boms/${bomId}`, data)
}
