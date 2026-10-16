export type Provider = 'anthropic' | 'openai' | 'compatible'
export type AuthHeader = 'bearer' | 'x-api-key'

export type AiSettingsIn = {
  provider: Provider
  api_key: string | null
  base_url: string | null
  auth_header: AuthHeader
  fast_model: string
  smart_model: string
}

export type AiSettingsOut = {
  configured: boolean
  source: 'app' | 'env' | 'none'
  provider: Provider | null
  base_url: string | null
  auth_header: AuthHeader
  fast_model: string | null
  smart_model: string | null
  has_key: boolean
  key_hint: string | null
}

export type Preset = {
  id: string
  label: string
  provider: Provider
  base_url: string | null
  auth_header: AuthHeader
  fast_model: string
  smart_model: string
  help: string
}

export type AiStatus = {
  configured: boolean
  provider: Provider | null
}
