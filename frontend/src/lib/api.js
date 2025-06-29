const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/api\/?$/, '')

export async function fetchApiInfo() {
  const url = `${API_BASE_URL.replace(/\/$/, '')}/api`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }
  return response.json()
}
