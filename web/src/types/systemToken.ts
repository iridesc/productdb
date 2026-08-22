export interface SystemToken {
  id: string
  name: string
  description?: string | null
  token_prefix: string
  is_active: boolean
  expires_at?: string | null
  last_used_at?: string | null
  created_by: string
  created_at: string
  updated_at: string
}

export interface SystemTokenCreate {
  name: string
  description?: string | null
  expires_at?: string | null
}

export interface SystemTokenUpdate {
  name?: string
  description?: string | null
  is_active?: boolean
  expires_at?: string | null
}

export interface SystemTokenCreated extends SystemToken {
  token: string
}
