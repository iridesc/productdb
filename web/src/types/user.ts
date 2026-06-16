export interface User {
  id: string
  username: string
  is_active: boolean
  is_superuser: boolean
  can_view_dashboard: boolean
  can_manage_materials: boolean
  can_manage_sales: boolean
  can_manage_production: boolean
  can_manage_inventory: boolean
  can_manage_users: boolean
  can_create_sales: boolean
  can_create_production: boolean
  created_at: string
}

export interface UserCreate {
  username: string
  password: string
  can_view_dashboard?: boolean
  can_manage_materials?: boolean
  can_manage_sales?: boolean
  can_manage_production?: boolean
  can_manage_inventory?: boolean
  can_manage_users?: boolean
  can_create_sales?: boolean
  can_create_production?: boolean
}

export interface UserUpdate {
  username?: string
  is_active?: boolean
  is_superuser?: boolean
  can_view_dashboard?: boolean
  can_manage_materials?: boolean
  can_manage_sales?: boolean
  can_manage_production?: boolean
  can_manage_inventory?: boolean
  can_manage_users?: boolean
  can_create_sales?: boolean
  can_create_production?: boolean
}
