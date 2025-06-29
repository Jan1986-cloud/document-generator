const RAW_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
// Support both with and without trailing `/api`
const API_BASE_URL = RAW_BASE_URL.replace(/\/?$/, '')

export async function fetchApiInfo() {
  const base = API_BASE_URL.endsWith('/api') ? API_BASE_URL : `${API_BASE_URL}/api`
  const response = await fetch(base)
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }
  return response.json()
}
