import { useEffect, useState, type FormEvent } from 'react'

import { getAiSettings, listModels, listPresets, saveAiSettings, testAiSettings } from './api'
import type { AiSettingsIn, AiSettingsOut, Preset } from './types'
import './ai.css'

type Props = {
  /** Called after a successful save. */
  onSaved?: (settings: AiSettingsOut) => void
}

const EMPTY: AiSettingsIn = {
  provider: 'anthropic',
  api_key: '',
  base_url: null,
  auth_header: 'bearer',
  fast_model: '',
  smart_model: '',
}

/** Pick the app-wide AI provider, test it, and save it. Admins only. */
export function AiSettingsForm({ onSaved }: Props) {
  const [presets, setPresets] = useState<Preset[]>([])
  const [presetId, setPresetId] = useState('')
  const [form, setForm] = useState<AiSettingsIn>(EMPTY)
  const [saved, setSaved] = useState<AiSettingsOut | null>(null)
  const [models, setModels] = useState<string[]>([])
  const [busy, setBusy] = useState<'test' | 'models' | 'save' | null>(null)
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null)

  useEffect(() => {
    Promise.all([listPresets(), getAiSettings()])
      .then(([presetList, current]) => {
        setPresets(presetList)
        setSaved(current)
        if (current.configured && current.provider) {
          setForm({
            provider: current.provider,
            api_key: '',
            base_url: current.base_url,
            auth_header: current.auth_header,
            fast_model: current.fast_model ?? '',
            smart_model: current.smart_model ?? '',
          })
          const match = presetList.find(
            (preset) =>
              preset.provider === current.provider &&
              (preset.base_url ?? null) === (current.base_url ?? null),
          )
          // An unknown URL is a custom server, not a preset with a fixed URL.
          const fallback =
            presetList.find((p) => p.provider === current.provider && !p.base_url) ??
            presetList.find((p) => p.provider === current.provider)
          setPresetId(match?.id ?? fallback?.id ?? '')
        } else {
          applyPreset(presetList[0])
        }
      })
      .catch((err) => setMessage({ ok: false, text: errorText(err) }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function applyPreset(preset: Preset | undefined) {
    if (!preset) return
    setPresetId(preset.id)
    setModels([])
    setMessage(null)
    setForm({
      provider: preset.provider,
      api_key: '',
      base_url: preset.base_url,
      auth_header: preset.auth_header,
      fast_model: preset.fast_model,
      smart_model: preset.smart_model,
    })
  }

  function update(patch: Partial<AiSettingsIn>) {
    setForm((current) => ({ ...current, ...patch }))
  }

  async function run(kind: 'test' | 'models' | 'save', action: () => Promise<void>) {
    setBusy(kind)
    setMessage(null)
    try {
      await action()
    } catch (err) {
      setMessage({ ok: false, text: errorText(err) })
    } finally {
      setBusy(null)
    }
  }

  const loadModels = () =>
    run('models', async () => {
      const result = await listModels(form)
      setModels(result.models)
      const count = result.models.length
      setMessage({
        ok: count > 0,
        text: count
          ? `${count} model${count === 1 ? '' : 's'} found. Pick them in the model fields.`
          : 'The provider listed no models. Type the model names.',
      })
    })

  const test = () =>
    run('test', async () => {
      const result = await testAiSettings(form)
      setMessage({ ok: result.ok, text: result.ok ? `✓ ${result.message}` : result.message })
    })

  const save = (event: FormEvent) => {
    event.preventDefault()
    run('save', async () => {
      const result = await saveAiSettings(form)
      setSaved(result)
      update({ api_key: '' })
      setMessage({ ok: true, text: 'Saved. The whole app now uses this provider.' })
      onSaved?.(result)
    })
  }

  const preset = presets.find((item) => item.id === presetId)
  const keyIsSaved = saved?.configured && saved.provider === form.provider && saved.has_key
  const isCompatible = form.provider === 'compatible'

  return (
    <form className="ai-form" onSubmit={save}>
      {saved?.source === 'env' && (
        <p className="ai-form__note">
          Currently using the Anthropic key from the <code>.env</code> file. Saving here takes
          over.
        </p>
      )}

      <label>
        Provider
        <select value={presetId} onChange={(e) => applyPreset(presets.find((p) => p.id === e.target.value))}>
          {presets.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
            </option>
          ))}
        </select>
      </label>
      {preset && <p className="ai-form__help">{preset.help}</p>}

      {isCompatible && (
        <>
          <label>
            Base URL
            <input
              type="url"
              required
              placeholder="https://example.com/v1"
              value={form.base_url ?? ''}
              onChange={(e) => update({ base_url: e.target.value })}
            />
          </label>
          <label>
            Key header
            <select
              value={form.auth_header}
              onChange={(e) => update({ auth_header: e.target.value as AiSettingsIn['auth_header'] })}
            >
              <option value="bearer">Authorization: Bearer</option>
              <option value="x-api-key">x-api-key</option>
            </select>
          </label>
        </>
      )}

      <label>
        API key
        <input
          type="password"
          autoComplete="off"
          placeholder={
            keyIsSaved
              ? `Saved${saved?.key_hint ? ` (${saved.key_hint})` : ''}. Leave empty to keep it.`
              : 'Paste your key'
          }
          value={form.api_key ?? ''}
          onChange={(e) => update({ api_key: e.target.value })}
        />
      </label>

      <div className="ai-form__models">
        <label>
          Fast model <span>(lookups, checks)</span>
          <input
            required
            list="ai-models"
            value={form.fast_model}
            onChange={(e) => update({ fast_model: e.target.value })}
          />
        </label>
        <label>
          Smart model <span>(summary, feed, podcast, video)</span>
          <input
            required
            list="ai-models"
            value={form.smart_model}
            onChange={(e) => update({ smart_model: e.target.value })}
          />
        </label>
        <datalist id="ai-models">
          {models.map((model) => (
            <option key={model} value={model} />
          ))}
        </datalist>
      </div>

      {message && (
        <p className={message.ok ? 'users__notice' : 'users__error'}>{message.text}</p>
      )}

      <div className="ai-form__actions">
        <button type="button" onClick={loadModels} disabled={busy !== null}>
          {busy === 'models' ? 'Loading…' : 'Load models'}
        </button>
        <button type="button" onClick={test} disabled={busy !== null}>
          {busy === 'test' ? 'Testing…' : 'Test connection'}
        </button>
        <button className="users__primary" type="submit" disabled={busy !== null}>
          {busy === 'save' ? 'Saving…' : 'Save'}
        </button>
      </div>
    </form>
  )
}

function errorText(err: unknown): string {
  return err instanceof Error ? err.message : 'Something went wrong.'
}
