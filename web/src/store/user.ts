import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>('')
  const userInfo = ref<any>(null)
  const roles = ref<string[]>([])

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUserInfo(info: any) {
    userInfo.value = info
  }

  function setRoles(roleList: string[]) {
    roles.value = roleList
  }

  function hasRole(role: string): boolean {
    return roles.value.includes('admin') || roles.value.includes(role)
  }

  function isOperator(): boolean {
    return hasRole('operator')
  }

  function isWorker(): boolean {
    return hasRole('worker')
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    roles.value = []
    localStorage.removeItem('token')
  }

  return {
    token,
    userInfo,
    roles,
    setToken,
    setUserInfo,
    setRoles,
    hasRole,
    isOperator,
    isWorker,
    logout
  }
})