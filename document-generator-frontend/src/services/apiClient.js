// API Client configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL
    this.defaultHeaders = {
      'Content-Type': 'application/json'
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    
    // Get auth token
    const token = localStorage.getItem('auth_token')
    
    // Prepare headers
    const headers = {
      ...this.defaultHeaders,
      ...options.headers
    }
    
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    // Prepare request config
    const config = {
      method: options.method || 'GET',
      headers,
      ...options
    }

    // Add body for non-GET requests
    if (options.body && config.method !== 'GET') {
      if (typeof options.body === 'object') {
        config.body = JSON.stringify(options.body)
      } else {
        config.body = options.body
      }
    }

    try {
      const response = await fetch(url, config)
      
      // Handle 401 Unauthorized
      if (response.status === 401) {
        localStorage.removeItem('auth_token')
        window.location.href = '/login'
        throw new Error('Sessie verlopen. Log opnieuw in.')
      }

      // Parse response
      let data
      const contentType = response.headers.get('content-type')
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json()
      } else {
        data = await response.text()
      }

      // Handle error responses
      if (!response.ok) {
        const errorMessage = data?.message || data?.error || `HTTP ${response.status}: ${response.statusText}`
        throw new Error(errorMessage)
      }

      return {
        data,
        status: response.status,
        headers: response.headers
      }
    } catch (error) {
      // Network or parsing errors
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Netwerkfout. Controleer uw internetverbinding.')
      }
      
      throw error
    }
  }

  // HTTP method helpers
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString()
    const url = queryString ? `${endpoint}?${queryString}` : endpoint
    
    return this.request(url, {
      method: 'GET'
    })
  }

  async post(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body
    })
  }

  async put(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body
    })
  }

  async patch(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'PATCH',
      body
    })
  }

  async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE'
    })
  }

  // File upload helper
  async uploadFile(endpoint, file, additionalData = {}) {
    const formData = new FormData()
    formData.append('file', file)
    
    // Add additional data to form
    Object.keys(additionalData).forEach(key => {
      formData.append(key, additionalData[key])
    })

    return this.request(endpoint, {
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type for FormData, let browser set it with boundary
      }
    })
  }

  // Download helper
  async downloadFile(endpoint, filename) {
    const token = localStorage.getItem('auth_token')
    const headers = {}
    
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'GET',
      headers
    })

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`)
    }

    const blob = await response.blob()
    
    // Create download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }
}

// Create and export API client instance
export const apiClient = new ApiClient(API_BASE_URL)

// Export for testing or custom instances
export { ApiClient }

