import { useCallback, useEffect, useState } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../lib/api'
import { useI18n } from '../contexts/I18nContext'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { Badge, Button, Card, DemoReadOnlyNotice, EmptyState, ErrorState, Input, Modal, Select, Spinner } from '../components/ui'
import type { Crop, CropProfit, Farm } from '../types'

const rs = (n: number) => `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

function daysSince(dateStr: string | null): number | null {
  if (!dateStr) return null
  const diff = Date.now() - new Date(dateStr).getTime()
  return Math.floor(diff / 86_400_000)
}

export default function Crops() {
  const { t } = useI18n()
  const { isReadOnly } = useAuth()
  const { push } = useToast()
  const { data: farms } = useApi<Farm[]>('/farms')
  const { data: profits, refresh: refreshProfits } = useApi<CropProfit[]>('/analytics/crops')
  const [allCrops, setAllCrops] = useState<Crop[] | null>(null)
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({
    farm_id: '', name: '', area_acres: '1', sowing_date: '',
    expected_yield_quintal: '', expected_price_per_quintal: '',
  })

  const reload = useCallback(async () => {
    if (!farms) return
    try {
      const lists = await Promise.all(farms.map((f) => api.get<Crop[]>(`/farms/${f.id}/crops`)))
      setAllCrops(lists.flat())
    } catch {
      setAllCrops([])
    }
  }, [farms])

  useEffect(() => { setAllCrops(null); reload() }, [reload])

  const save = async () => {
    const farmId = Number(form.farm_id)
    const payload: Record<string, unknown> = {
      name: form.name, area_acres: Number(form.area_acres),
      sowing_date: form.sowing_date || null,
      expected_yield_quintal: form.expected_yield_quintal ? Number(form.expected_yield_quintal) : null,
      expected_price_per_quintal: form.expected_price_per_quintal ? Number(form.expected_price_per_quintal) : null,
    }
    try {
      await api.post(`/farms/${farmId}/crops`, payload)
      setOpen(false)
      reload()
      refreshProfits()
      push('success', t('common.save'))
    } catch (e) {
      push('error', e instanceof Error ? e.message : t('err.generic'))
    }
  }

  const remove = async (farmId: number, id: number) => {
    if (!confirm('Delete this crop?')) return
    await api.delete(`/farms/${farmId}/crops/${id}`)
    reload()
    refreshProfits()
  }

  const profitOf = (id: number) => (profits ?? []).find((p) => p.crop_id === id)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-extrabold text-green-900">{t('nav.crops')}</h1>
        <Button onClick={() => setOpen(true)} disabled={isReadOnly || (farms ?? []).length === 0}>
          ＋ {t('crops.add')}
        </Button>
      </div>

      {isReadOnly && <DemoReadOnlyNotice />}

      {allCrops !== null && allCrops.length === 0 && <EmptyState icon="🌾" message={t('common.empty')} />}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {(allCrops ?? []).map((c) => {
          const p = profitOf(c.id)
          const days = daysSince(c.sowing_date)
          const expectedProfit =
            c.expected_yield_quintal && c.expected_price_per_quintal
              ? c.expected_yield_quintal * c.expected_price_per_quintal - (p?.total_cost ?? 0)
              : null
          const tone = c.status === 'active' ? 'green' : c.status === 'harvested' ? 'amber' : 'gray'
          return (
            <Card key={c.id}>
              <div className="flex items-start justify-between">
                <h3 className="font-bold text-green-900">{c.name}</h3>
                <Badge tone={tone as 'green' | 'amber' | 'gray'}>{t(`crop.${c.status}`)}</Badge>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                {farms?.find((f) => f.id === c.farm_id)?.name}
                {days !== null && ` · ${days} ${t('crop.daysSinceSowing')}`}
              </p>
              <div className="mt-2 grid grid-cols-2 gap-1 text-sm">
                <span>🧾 {t('nav.expenses')}: <b>{rs(p?.total_cost ?? 0)}</b></span>
                <span>💰 {t('dash.netProfit')}: <b>{rs(p?.profit ?? 0)}</b></span>
                {c.expected_yield_quintal && (
                  <span>🌾 {t('crops.expectedYield')}: <b>{c.expected_yield_quintal} q</b></span>
                )}
                {expectedProfit !== null && (
                  <span>📈 {t('dash.totalRevenue')}: <b>~{rs(Math.max(expectedProfit, 0))}</b></span>
                )}
              </div>
              {/* lifecycle timeline */}
              <div className="mt-3 flex gap-1 text-[11px]">
                {(['active', 'harvested', 'sold'] as const).map((s) => {
                  const done = s === 'active' || (s === 'harvested' && c.status !== 'active') || (s === 'sold' && c.status === 'sold')
                  return (
                    <span key={s} className={`flex-1 rounded px-1.5 py-0.5 text-center ${
                      done ? 'bg-green-700 text-white' : 'bg-gray-100 text-gray-400'}`}>
                      {t(`crop.${s}`)}
                    </span>
                  )
                })}
              </div>
              <div className="mt-3">
                <Button variant="danger" onClick={() => remove(c.farm_id, c.id)} disabled={isReadOnly}>{t('common.delete')}</Button>
              </div>
            </Card>
          )
        })}
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title={t('crops.add')}>
        <div className="space-y-3">
          <Select label={t('nav.farms')} value={form.farm_id}
                  onChange={(e) => setForm({ ...form, farm_id: e.target.value })}>
            <option value="">—</option>
            {(farms ?? []).map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
          </Select>
          <Input label={t('nav.crops')} value={form.name}
                 onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label={t('farms.area')} type="number" step="0.1" min="0.1" value={form.area_acres}
                 onChange={(e) => setForm({ ...form, area_acres: e.target.value })} />
          <Input label={t('crops.sowing')} type="date" value={form.sowing_date}
                 onChange={(e) => setForm({ ...form, sowing_date: e.target.value })} />
          <div className="grid grid-cols-2 gap-2">
            <Input label={t('crops.expectedYield')} type="number" step="0.1" value={form.expected_yield_quintal}
                   onChange={(e) => setForm({ ...form, expected_yield_quintal: e.target.value })} />
            <Input label={t('crops.expectedPrice')} type="number" step="1" value={form.expected_price_per_quintal}
                   onChange={(e) => setForm({ ...form, expected_price_per_quintal: e.target.value })} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>{t('common.cancel')}</Button>
            <Button onClick={save} disabled={!form.name || !form.farm_id}>{t('common.save')}</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
