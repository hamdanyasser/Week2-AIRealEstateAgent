// Thin wrapper around the FastAPI backend. No business logic lives here —
// this file only knows how to POST a query and unwrap the response.

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

async function postJson(path, body) {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    let detail
    try {
      const body = await response.json()
      detail = body.detail
    } catch {
      detail = response.statusText
    }
    // detail is a string for 500/503, but an array of objects for 422 (Pydantic).
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((e) => e.msg).join('; ')
          : null
    const error = new Error(message || `Request failed (${response.status})`)
    error.status = response.status
    throw error
  }

  return response.json()
}

export async function extractProperty(query, promptVersion = 'v2') {
  return postJson('/extract', {
    query,
    prompt_version: promptVersion,
  })
}

export async function analyzeProperty(
  query,
  promptVersion = 'v2',
  reviewedFeatures = null,
) {
  return postJson('/predict', {
    query,
    prompt_version: promptVersion,
    reviewed_features: reviewedFeatures,
  })
}
