import { useCallback, useEffect, useState } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../lib/api'
import { useI18n } from '../contexts/I18nContext'
import { useToast } from '../contexts/ToastContext'
import { Button, Card, EmptyState, Input, Select, Spinner } from '../components/ui'
import type { Crop, Farm, Sale } from '../types'

const rs = (n: number) => `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function Sales() {
  const { t } = useI18n()
  const { push } = useToast()
  const { data: farms } = useApi<Farm[]>('/farms')
  const [crops, setCrops] = useState<Crop[]>([])
  const [sales, setSales] = useState<Record<number, Sale[]>>({})
  const [cropId, setCropId] = useState('')
  const [form, setForm] = useState({ sale_date: '', quantity_quintal: '', price_per_quintal: '', transport_cost: '0', other_charges: '0', buyer: '' })
  const [busy, setBusy] = useState(false)

  const reload = useCallback(async () => {
    if (!farms) return
    try {
      const lists = await Promise.all(farms.map((f) => api.get<Crop[]>(`/farms/${f.id}/crops`)))
      const all = lists.flat()
      setCrops(all)
      const entries = await Promise.all(all.map(async (c) =>
        [c.id, await api.get<Sale[]>(`/crops/${c.id}/sales`)] as const))
      setSales(Object.fromEntries(entries))
    } catch { /* silent */ }
  }, [farms])

  useEffect(() => { reload() }, [reload])

  const save = async () => {
    if (!cropId || !form.quantity_quintal || !form.price_per_quintal) return
    setBusy(true)
    try {
      await api.post(`/crops/${cropId}/sales`, {
        sale_date: form.sale_date || new Date().toISOString().slice(0, 10),
        quantity_quintal: Number(form.quantity_quintal),
        price_per_quintal: Number(form.price_per_quintal),
        transport_cost: Number(form.transport_cost || 0),
        other_charges: Number(form.other_charges || 0),
        buyer: form.buyer || undefined,
      })
      setForm({ sale_date: '', quantity_quintal: '', price_per_quintal: '', transport_cost: '0', other_charges: '0', buyer: '' })
      reload()
      push('success', t('common.save'))
    } catch (e) {
      push('error', e instanceof Error ? e.message : t('err.generic'))
    } finally {
      setBusy(false)
    }
  }

  const net = (s: Sale) => s.quantity_quintal * s.price_per_quintal - s.transport_cost - s.other_charges
  const draftNet = Number(form.quantity_quintal || 0) * Number(form.price_per_quintal || 0)
    - Number(form.transport_cost || 0) - Number(form.other_charges || 0)

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold text-green-900">{t('nav.sales')}</h1>

      <Card>
        <div className="grid gap-2 sm:grid-cols-3">
          <Select label={t('nav.crops')} value={cropId} onChange={(e) => setCropId(e.target.value)}>
            <option value="">—</option>
            {crops.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <Input label={t('sales.quantity')} type="number" step="0.1" min="0.1" value={form.quantity_quintal}
                 onChange={(e) => setForm({ ...form, quantity_quintal: e.target.value })} />
          <Input label={t('sales.price')} type="number" step="1" min="1" value={form.price_per_quintal}
                 onChange={(e) => setForm({ ...form, price_per_quintal: e.target.value })} />
          <Input label={t('sales.transport')} type="number" step="1" min="0" value={form.transport_cost}
                 onChange={(e) => setForm({ ...form, transport_cost: e.target.value })} />
          <Input label={t('sales.other')} type="number" step="1" min="0" value={form.other_charges}
                 onChange={(e) => setForm({ ...form, other_charges: e.target.value })} />
          <Input label={t('sales.buyer')} value={form.buyer}
                 onChange={(e) => setForm({ ...form, buyer: e.target.value })} />
        </div>
        {draftNet > 0 && (
          <p className="mt-2 text-sm text-gray-600">{t('sales.net')}: <b className="text-green-700">{rs(draftNet)}</b></p>
        )}
        <div className="mt-2 flex justify-end">
          <Button onClick={save} disabled={busy || !cropId}>{t('sales.record')}</Button>
        </div>
      </Card>

      {crops.length === 0 ? <Spinner /> : crops.map((c) => {
        const list = sales[c.id] ?? []
        const total = list.reduce((s, x) => s + net(x), 0)
        return (
          <Card key={c.id}>
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-green-900">{c.name}</h3>
              {list.length > 0 && <span className="text-sm font-semibold text-green-700">{rs(total)}</span>}
            </div>
            {list.length === 0 ? <EmptyState icon="💰" message={t('common.empty')} /> : (
              <ul className="mt-2 space-y-1 text-sm">
                {list.map((s) => (
                  <li key={s.id} className="flex justify-between rounded bg-gray-50 px-3 py-1.5">
                    <span>📅 {s.sale_date} · {s.quantity_quintal} q @ {rs(s.price_per_quintal)}</span>
                    <span><b>{rs(net(s))}</b></span>
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
