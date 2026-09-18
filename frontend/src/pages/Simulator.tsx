import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../lib/api'
import { useI18n } from '../contexts/I18nContext'
import { Button, Card, Input, Select } from '../components/ui'
import type { Crop, CropProfit, Farm, SimulatorResult } from '../types'

const rs = (n: number) => `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function Simulator() {
  const { t } = useI18n()
  const { data: farms } = useApi<Farm[]>('/farms')
  const { data: profits } = useApi<CropProfit[]>('/analytics/crops')
  const [results, setResults] = useState<Record<number, SimulatorResult[]>>({})
  const [busy, setBusy] = useState(false)
  const [cropId, setCropId] = useState('')
  const [price, setPrice] = useState('')

  const crops = (profits ?? []).map((p) => ({ id: p.crop_id, name: p.crop_name }))
  const selected = (profits ?? []).find((p) => p.crop_id === Number(cropId))

  const run = async () => {
    if (!selected) return
    setBusy(true)
    try {
      const basePrice = Number(price) || selected.break_even_price_per_quintal || 5000
      const points = [0.9, 1, 1.1, 1.2].map((m) => Math.round(basePrice * m))
      const scenarios: Array<{ label: string; price: number; prod?: number; cost: number }> = [
        ...points.map((p) => ({ label: `${t('sim.price')} ${rs(p)}`, price: p, cost: 1 })),
        { label: `${t('prod.actualYield')} −15%`, price: basePrice, prod: (selected.produced_quintal || selected.expected_yield_quintal || 0) * 0.85, cost: 1 },
        { label: `${t('dash.totalInvestment')} +20%`, price: basePrice, cost: 1.2 },
      ]
      const outs: SimulatorResult[] = []
      for (const s of scenarios) {
        outs.push(await api.post<SimulatorResult>(`/analytics/simulator/${selected.crop_id}`, {
          price_per_quintal: s.price,
          production_quintal: s.prod ?? undefined,
          cost_multiplier: s.cost,
        }))
      }
      setResults({ ...results, [selected.crop_id]: outs })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold text-green-900">{t('sim.title')}</h1>

      <Card>
        <div className="grid gap-2 sm:grid-cols-3">
          <Select label={t('nav.crops')} value={cropId} onChange={(e) => setCropId(e.target.value)}>
            <option value="">—</option>
            {crops.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <Input label={t('sim.price')} type="number" step="100" min="1" value={price}
                 onChange={(e) => setPrice(e.target.value)}
                 placeholder={selected?.break_even_price_per_quintal
                   ? `≥ ${Math.round(selected.break_even_price_per_quintal)}` : ''} />
          <div className="flex items-end">
            <Button className="w-full" onClick={run} disabled={!cropId || busy}>{t('sim.run')}</Button>
          </div>
        </div>
        {selected?.break_even_price_per_quintal && (
          <p className="mt-2 text-sm text-gray-600">
            {t('sim.breakEven')}: <b className="text-amber-700">{rs(selected.break_even_price_per_quintal)}/q</b>
            {' '}(sell above this to profit)
          </p>
        )}
      </Card>

      {results[Number(cropId)] && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {results[Number(cropId)].map((r, i) => (
            <Card key={i} className={r.profit >= 0 ? 'border-t-4 border-green-600' : 'border-t-4 border-red-500'}>
              <p className="text-xs uppercase tracking-wide text-gray-400">{t('sim.scenarios')} #{i + 1}</p>
              <p className="mt-1 text-2xl font-extrabold {r.profit >= 0 ? 'text-green-700' : 'text-red-600'}"
                 style={{ color: r.profit >= 0 ? '#15803d' : '#dc2626' }}>
                {rs(r.profit)}
              </p>
              <p className="text-sm text-gray-500">{t('dash.totalRevenue')}: {rs(r.revenue)}</p>
              <p className="text-sm text-gray-500">{t('dash.totalInvestment')}: {rs(r.total_cost)}</p>
              <p className="text-sm text-gray-500">{t('sim.breakEven')}: {rs(r.break_even_price_per_quintal)}/q</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
