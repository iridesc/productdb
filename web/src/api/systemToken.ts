import request from '@/utils/request'
import type { SystemToken, SystemTokenCreate, SystemTokenCreated, SystemTokenUpdate } from '@/types/systemToken'

export const getSystemTokens = () => request.get<SystemToken[]>('/system-tokens')
export const createSystemToken = (data: SystemTokenCreate) =>
  request.post<SystemTokenCreated>('/system-tokens', data)
export const updateSystemToken = (id: string, data: SystemTokenUpdate) =>
  request.put<SystemToken>(`/system-tokens/${id}`, data)
export const deleteSystemToken = (id: string) => request.delete(`/system-tokens/${id}`)
