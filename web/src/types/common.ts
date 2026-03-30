// 通用分页响应
export interface PageResponse<T> {
  total: number
  items: T[]
}

// 通用 ID 类型
export type ID = string

// 通用日期类型
export type DateTime = string
export type DateType = string