import type { AiSettingsIn, AiSettingsOut, AiStatus, Preset } from './types'

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api/ai${path}`, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    const detail =
      typeof data?.detail === 'string' ? data.detail : `Request failed (${response.status}).`
    throw new Error(detail)
  }
  return response.json()
}

export const aiStatus = () => request<AiStatus>('GET', '/status')
export const listPresets = () => request<Preset[]>('GET', '/presets')
export const getAiSettings = () => request<AiSettingsOut>('GET', '/settings')
export const saveAiSettings = (settings: AiSettingsIn) =>
  request<AiSettingsOut>('PUT', '/settings', settings)
export const testAiSettings = (settings: AiSettingsIn) =>
  request<{ ok: boolean; message: string }>('POST', '/test', settings)
export const listModels = (settings: AiSettingsIn) =>
  request<{ models: string[] }>('POST', '/models', settings)
