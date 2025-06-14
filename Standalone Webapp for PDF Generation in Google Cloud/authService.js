import { apiClient } from './apiClient'

export const authService = {
  async login(email, password) {
    const response = await apiClient.post('/auth/login', {
      email,
      password
    })
    return response.data
  },

  async register(userData) {
    const response = await apiClient.post('/auth/register', userData)
    return response.data
  },

  async logout() {
    try {
      await apiClient.post('/auth/logout')
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error)
    }
  },

  async getProfile() {
    const response = await apiClient.get('/users/profile')
    return response.data.user
  },

  async updateProfile(profileData) {
    const response = await apiClient.put('/users/profile', profileData)
    return response.data.user
  },

  async requestPasswordReset(email) {
    const response = await apiClient.post('/auth/request-password-reset', {
      email
    })
    return response.data
  },

  async resetPassword(token, newPassword) {
    const response = await apiClient.post('/auth/reset-password', {
      token,
      password: newPassword
    })
    return response.data
  },

  async verifyEmail(token) {
    const response = await apiClient.post('/auth/verify-email', {
      token
    })
    return response.data
  },

  async resendVerification(email) {
    const response = await apiClient.post('/auth/resend-verification', {
      email
    })
    return response.data
  },

  async refreshToken() {
    const response = await apiClient.post('/auth/refresh')
    return response.data
  }
}

