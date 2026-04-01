import request from '@/utils/request'
import type { ID, DateTime } from '@/types/common'

export interface MaterialImage {
  id: ID
  material_id: ID
  image_url: string
  sort_order: number
  created_at: DateTime
}

export function getMaterialImages(materialId: string) {
  return request.get<MaterialImage[]>(`/materials/${materialId}/images`)
}

export function uploadMaterialImage(materialId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request.post<MaterialImage>(`/materials/${materialId}/images`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 30000,
  })
}

export function deleteMaterialImage(imageId: string) {
  return request.delete(`/materials/images/${imageId}`)
}

export function updateImageSort(imageId: string, sortOrder: number) {
  return request.put(`/materials/images/${imageId}/sort?sort_order=${sortOrder}`)
}
