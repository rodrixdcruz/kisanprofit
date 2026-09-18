import { useCallback, useEffect, useState } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../lib/api'
import { useI18n } from '../contexts/I18nContext'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { Badge, Button, Card, DemoReadOnlyNotice, EmptyState, Input, Select, Spinner } from '../components/ui'
import type { Crop, Farm, Production } from '../types'

export default function Production() {
  const { t } = useI18n()
  const { isReadOnly } = useAuth()
  const { push } = useToast()
  const { data: farms } = useApi<Farm[]>('/farms')
  const [crops, setCrops] = useState<Crop[]>([])
  const [records, setRecords] = useState<Record<number, Production[]>>({})
  const [cropId, setCropId] = useState('')
  const [form, setForm] = useState({ harvest_date: '', actual_yield_quintal: '', note: '' })
  const [busy, setBusy] = useState(false)

  const reload = useCallback(async () => {
    if (!farms) return
    try {
      const lists = await Promise.all(farms.map((f) => api.get<Crop[]>(`/farms/${f.id}/crops`)))
      const all = lists.flat()
      setCrops(all)
      const entries = await Promise.all(all.map(async (c) =>
        [c.id, await api.get<Production[]>(`/crops/${c.id}/production`)] as const))
      setRecords(Object.fromEntries(entries))
    } catch { /* silent */ }
  }, [farms])

  useEffect(() => { reload() }, [reload])

  const save = async () => {
    if (!cropId || !form.actual_yield_quintal) return
    setBusy(true)
    try {
      await api.post(`/crops/${cropId}/production`, {
        harvest_date: form.harvest_date || new Date().toISOString().slice(0, 10),
        actual_yield_quintal: Number(form.actual_yield_quintal),
        note: form.note || undefined,
      })
      setForm({ harvest_date: '', actual_yield_quintal: '', note: '' })
      reload()
      push('success', t('common.save'))
    } catch (e) {
      push('error', e instanceof Error ? e.message : t('err.generic'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold text-green-900">{t('nav.production')}</h1>

      {isReadOnly && <DemoReadOnlyNotice />}

      <Card>
        <div className="grid gap-2 sm:grid-cols-3">
          <Select label={t('nav.crops')} value={cropId} onChange={(e) => setCropId(e.target.value)}>
            <option value="">—</option>
            {crops.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <Input label={t('prod.harvestDate')} type="date" value={form.harvest_date}
                 onChange={(e) => setForm({ ...form, harvest_date: e.target.value })} />
          <Input label={t('prod.actualYield')} type="number" step="0.1" min="0.1"
                 value={form.actual_yield_quintal}
                 onChange={(e) => setForm({ ...form, actual_yield_quintal: e.target.value })} />
        </div>
        <div className="mt-2 flex justify-end">
          <Button onClick={save} disabled={busy || isReadOnly || !cropId}>{t('prod.record')}</Button>
        </div>
      </Card>

      {crops.length === 0 ? <Spinner /> : crops.map((c) => {
        const recs = records[c.id] ?? []
        const produced = recs.reduce((s, r) => s + r.actual_yield_quintal, 0)
        const variance = c.expected_yield_quintal && produced > 0
          ? (produced - c.expected_yield_quintal) / c.expected_yield_quintal * 100 : null
        return (
          <Card key={c.id}>
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-green-900">{c.name}</h3>
              {variance !== null && (
                <Badge tone={variance >= -2 ? 'green' : variance >= -10 ? 'amber' : 'red'}>
                  {variance >= 0 ? '+' : ''}{variance.toFixed(1)}% {t('prod.expectedVsActual')}
                </Badge>
              )}
            </div>
            {c.expected_yield_quintal && (
              <p className="mt-1 text-sm text-gray-600">
                {t('crops.expectedYield')}: <b>{c.expected_yield_quintal} q</b> ·
                {t('prod.actualYield')}: <b>{produced || '—'} q</b>
              </p>
            )}
            {recs.length === 0 ? <EmptyState icon="🌾" message={t('common.empty')} /> : (
              <ul className="mt-2 space-y-1 text-sm">
                {recs.map((r) => (
                  <li key={r.id} className="flex justify-between rounded bg-gray-50 px-3 py-1.5">
                    <span>📅 {r.harvest_date}</span><span><b>{r.actual_yield_quintal} q</b></span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        )
      })}
    </div>
  )
}
