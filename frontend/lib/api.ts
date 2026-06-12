const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function getToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('tc_token')
}

export function setToken(t: string) { localStorage.setItem('tc_token', t) }
export function clearToken() { localStorage.removeItem('tc_token') }

export function getUser() {
  if (typeof window === 'undefined') return null
  const u = localStorage.getItem('tc_user')
  return u ? JSON.parse(u) : null
}

export function setUser(u: object) { localStorage.setItem('tc_user', JSON.stringify(u)) }

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${API}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export async function login(email: string, password: string) {
  const form = new URLSearchParams({ username: email, password })
  const res = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  })
  if (!res.ok) throw new Error('Invalid credentials')
  return res.json()
}

export async function register(email: string, username: string, password: string) {
  const res = await fetch(`${API}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password }),
  })
  if (!res.ok) {
    const e = await res.json()
    throw new Error(e.detail || 'Registration failed')
  }
  return res.json()
}

export async function* streamChat(message: string, history: { role: string; content: string }[]) {
  const token = getToken()
  const res = await fetch(`${API}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ message, history }),
  })
  if (!res.ok) throw new Error('Stream failed')
  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          yield JSON.parse(line.slice(6))
        } catch {}
      }
    }
  }
}
