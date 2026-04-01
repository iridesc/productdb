import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { showDialog } from 'vant'
import router from '../router'

const instance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

export function handleError(error: any): string {
  let errorMessage = '网络错误'
  
  if (error.response) {
    const data = error.response.data
    if (data) {
      if (data.detail) {
        if (Array.isArray(data.detail) && data.detail.length > 0) {
          if (error.response.status === 422) {
            const errors: string[] = []
            data.detail.forEach((item: any) => {
              if (item.loc) {
                const field = item.loc[item.loc.length - 1]
                const msg = item.msg || item.message
                if (field && msg) {
                  errors.push(`${field}: ${msg}`)
                } else if (msg) {
                  errors.push(msg)
                }
              } else if (item.msg || item.message) {
                errors.push(item.msg || item.message)
              }
            })
            errorMessage = errors.join('；')
          } else {
            errorMessage = data.detail[0].msg || data.detail[0].message || errorMessage
          }
        } else if (typeof data.detail === 'string') {
          errorMessage = data.detail
        } else if (data.detail.error) {
          errorMessage = data.detail.error
          if (Array.isArray(data.detail.fields) && data.detail.fields.length > 0) {
            errorMessage += '：' + data.detail.fields.join('；')
          }
        }
      } else if (data.message) {
        errorMessage = data.message
      }
    }
    
    errorMessage = `错误 ${error.response.status}: ${errorMessage}`
  } else if (error.message) {
    errorMessage = error.message
  }

  return errorMessage
}

export function showMessage(message: string) {
  showDialog({
    title: '提示',
    message: message,
    confirmButtonText: '确定'
  })
}

function showError(message: string) {
  showDialog({
    title: '错误',
    message: message,
    confirmButtonText: '确定'
  })
}

instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    const errorMessage = handleError(error)
    showError(errorMessage)
    return Promise.reject(error)
  }
)

instance.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      if (error.response.status === 401) {
        localStorage.removeItem('token')
        router.push('/login')
        showError('登录已过期，请重新登录')
      } else {
        const errorMessage = handleError(error)
        showError(errorMessage)
      }
    } else {
      showError('网络连接失败')
    }
    return Promise.reject(error)
  }
)

interface Request {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
}

const request = instance as unknown as Request

export default request
