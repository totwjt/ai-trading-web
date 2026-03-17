export interface User {
  id: string
  username: string
  email: string
  avatar?: string
  balance: number
  createdAt: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}