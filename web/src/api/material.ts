import request from '@/utils/request'
import type { Material, MaterialCreate, MaterialUpdate } from '@/types/material'
import type { PageResponse } from '@/types/common'

// 物料列表
export function getMaterials(params: {
  page?: number
  page_size?: number
  keyword?: string
  is_active?: boolean
}) {
  return request.get<{ total: number; items: Material[] }>('/materials', { params })
}

// 物料详情
export function getMaterial(id: string) {
  return request.get<Material>(`/materials/${id}`)
}

// 创建物料
export function createMaterial(data: MaterialCreate) {
  return request.post<Material>('/materials', data)
}

// 更新物料
export function updateMaterial(id: string, data: MaterialUpdate) {
  return request.put<Material>(`/materials/${id}`, data)
}

// 删除物料
export function deleteMaterial(id: string) {
  return request.delete(`/materials/${id}`)
}

// 获取标签列表
export function getTags() {
  return request.get<any[]>('/tags')
}

// 创建标签
export function createTag(data: { name: string; color?: string }) {
  return request.post<any>('/tags', data)
}

// 删除标签
export function deleteTag(id: string) {
  return request.delete(`/tags/${id}`)
}

// 物料图片上传
export function uploadMaterialImage(materialId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/materials/${materialId}/images`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 删除物料图片
export function deleteMaterialImage(materialId: string, imageId: string) {
  return request.delete(`/materials/${materialId}/images/${imageId}`)
}

// 获取物料图片
export function getMaterialImages(materialId: string) {
  return request.get<any[]>(`/materials/${materialId}/images`)
}