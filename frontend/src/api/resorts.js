const BASE = '/api'

function buildQueryString(filters) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value === null || value === undefined) continue
    if (Array.isArray(value)) {
      value.forEach(v => params.append(key, v))
    } else {
      params.set(key, String(value))
    }
  }
  return params.toString()
}

async function apiFetch(path) {
  const res = await fetch(path)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Request failed: ${res.status}`)
  }
  return res.json()
}

export async function fetchResorts(filters = {}) {
  const qs = buildQueryString(filters)
  return apiFetch(`${BASE}/resorts${qs ? `?${qs}` : ''}`)
}

export async function fetchResort(id) {
  return apiFetch(`${BASE}/resorts/${encodeURIComponent(id)}`)
}

export async function fetchMeta() {
  return apiFetch(`${BASE}/meta`)
}
