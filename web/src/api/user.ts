import request from '@/utils/request'
import type { User, UserCreate, UserUpdate } from '@/types/user'

export function getUsers() {
  return request.get<User[]>('/users')
}

export function getUser(id: string) {
  return request.get<User>(`/users/${id}`)
}

export function createUser(data: UserCreate) {
  return request.post<User>('/users', data)
}

export function updateUser(id: string, data: UserUpdate) {
  return request.put<User>(`/users/${id}`, data)
}

export function deleteUser(id: string) {
  return request.delete(`/users/${id}`)
}

export function updatePassword(userId: string, password: string) {
  return request.put(`/users/${userId}/password`, { password })
}
