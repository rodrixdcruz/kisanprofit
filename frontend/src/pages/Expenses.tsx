import { useEffect, useMemo, useRef, useState } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../lib/api'
import { useI18n } from '../contexts/I18nContext'
import { useToast } from '../contexts/ToastContext'
import { useVoice } from '../hooks/useVoice'
import { Button, Card, EmptyState, ErrorState, Input, Select, Spinner } from '../components/ui'
import type { Crop, Expense, Farm } from '../types'

const CATEGORIES = ['seeds', 'fertilizer', 'pesticide', 'labor', 'fuel', 'irrigation',
  'equipment', 'transport', 'electricity', 'rent', 'insurance', 'other'] as const

const QUICK = [
  { cat: 'fertilizer', amount: 2500 }, { cat: 'labor', amount: 1500 },
  { cat: 'fuel', amount: 500 }, { cat: 'seeds', amount: 1000 },
] as const

const rs = (n: number) => `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

interface Stats { total: number; count: number; this_month: number; average: number; largest_category: string | null; largest_category_amount: number }

export default function Expenses() {
  const { t } = useI18n()
  const { push } = useToast()
  const voice = useVoice()
  const fileRef = useRef<HTMLInputElement>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [rows, setRows] = useState<Expense[] | null>(null)
  const [search, setSearch] = useState('')
  const [catFilter, setCatFilter] = useState('')
  const [sort, setSort] = useState('date_desc')
  const [open, setOpen] = useState(false)
  const [cropId, setCropId] = useState('')
  const [form, setForm] = useState({ category: 'fertilizer', amount: '', date: '', note: '', crop_id: '' })
  const [ocrBusy, setOcrBusy] = useState(false)

  const { data: farms } = useApi<Farm[]>('/farms')
  const [cropOptions, setCropOptions] = useState<Crop[]>([])

  useEffect(() => {
    if (!farms) return
    Promise.all(farms.map((f) => api.get<Crop[]>(`/farms/${f.id}/crops`)))
      .then((lists) => setCropOptions(lists.flat()))
      .catch(() => setCropOptions([]))
  }, [farms])

  const load = async () => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (catFilter) params.set('category', catFilter)
    params.set('sort', sort)
    const [list, st] = await Promise.all([
      api.get<Expense[]>(`/expenses?${params}`),
      api.get<Stats>('/expenses/stats'),
    ])
    setRows(list)
    setStats(st)
  }

  useMemo(() => { load().catch(() => push('error', t('err.network'))); return null }, [search, catFilter, sort])

  const save = async () => {
    const payload = {
      category: form.category,
      amount: Number(form.amount),
      spent_on: form.date || undefined,
      note: form.note || undefined,
      crop_id: form.crop_id ? Number(form.crop_id) : null,
      source: voice.transcript ? 'voice' : 'manual',
      ...(voice.transcript ? { note: form.note || `voice: ${voice.transcript}` } : {}),
    }
    try {
      await api.post('/expenses', payload)
      setOpen(false)
      setForm({ category: 'fertilizer', amount: '', date: '', note: '', crop_id: '' })
      voice.reset()
      load()
      push('success', t('common.save'))
    } catch (e) {
      push('error', e instanceof Error ? e.message : t('err.generic'))
    }
  }

  const quickAdd = async (cat: string, amount: number) => {
    await api.post('/expenses', { category: cat, amount })
    load()
    push('success', `${t(`cat.${cat}`)} ${rs(amount)}`)
  }

  const scanReceipt = async (file: File) => {
    setOcrBusy(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await api.post<{ amount: number | null; category: string | null; vendor: string | null; demo: boolean }>(
        '/ocr/receipt', fd)
      setForm((f) => ({
        ...f,
        amount: res.amount?.toString() ?? f.amount,
        category: res.category ?? f.category,
        note: res.vendor ? `receipt: ${res.vendor}` : f.note,
      }))
      setOpen(true)
      push(res.demo ? 'error' : 'success',
        res.demo ? 'OCR in demo mode — enter details manually' : 'Receipt read — please confirm')
    } finally {
      setOcrBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-extrabold text-green-900">{t('nav.expenses')}</h1>
        <Button onClick={() => setOpen(true)}>＋ {t('exp.add')}</Button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 gap-3 text-sm lg:grid-cols-4">
          <Card>Σ {t('dash.totalInvestment')}: <b>{rs(stats.total)}</b></Card>
          <Card>{t('dash.thisMonth')}: <b>{rs(stats.this_month)}</b></Card>
          <Card>Ø: <b>{rs(stats.average)}</b></Card>
          <Card>{t('dash.largestCategory')}: <b>{stats.largest_category ? t(`cat.${stats.largest_category}`) : '—'}</b></Card>
        </div>
      )}

      <Card>
        <div className="mb-3 text-sm font-semibold text-gray-600">{t('exp.quickAdd')}</div>
        <div className="flex flex-wrap gap-2">
          {QUICK.map(({ cat, amount }) => (
            <button key={cat} onClick={() => quickAdd(cat, amount)}
              className="btn-tap rounded-xl border border-dashed border-green-600 px-4 py-2 text-sm font-semibold text-green-800">
              {t(`cat.${cat}`)} {rs(amount)}
            </button>
          ))}
          <button onClick={() => fileRef.current?.click()} disabled={ocrBusy}
            className="btn-tap rounded-xl border border-dashed border-gray-400 px-4 py-2 text-sm text-gray-600">
            📷 {ocrBusy ? '…' : 'Scan receipt'}
          </button>
          <input ref={fileRef} type="file" accept="image/*" hidden
                 onChange={(e) => e.target.files?.[0] && scanReceipt(e.target.files[0])} />
        </div>
      </Card>

      <Card>
        <div className="grid gap-2 sm:grid-cols-3">
          <Input placeholder={t('exp.search')} value={search} onChange={(e) => setSearch(e.target.value)} />
          <Select value={catFilter} onChange={(e) => setCatFilter(e.target.value)}>
            <option value="">{t('exp.category')}: all</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{t(`cat.${c}`)}</option>)}
          </Select>
          <Select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="date_desc">Date ↓</option>
            <option value="date_asc">Date ↑</option>
            <option value="amount_desc">{t('exp.amount')} ↓</option>
            <option value="amount_asc">{t('exp.amount')} ↑</option>
          </Select>
        </div>
      </Card>

      {rows === null ? <Spinner /> : rows.length === 0 ? <EmptyState icon="🧾" message={t('common.empty')} /> : (
        <div className="space-y-2">
          {rows.map((e) => (
            <Card key={e.id} className="flex items-center justify-between">
              <div>
                <p className="font-semibold">{t(`cat.${e.category}`)}</p>
                <p className="text-xs text-gray-500">
                  {e.spent_on}{e.crop_id ? ` · crop #${e.crop_id}` : ''}
                  {e.source !== 'manual' && ` · ${e.source === 'voice' ? '🎙️' : '📷'} ${e.source}`}
                </p>
                {e.note && <p className="text-xs text-gray-400">{e.note}</p>}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-lg font-bold text-red-700">−{rs(e.amount)}</span>
                <Button variant="ghost" onClick={async () => {
                  if (!confirm('Delete?')) return
                  await api.delete(`/expenses/${e.id}`); load()
                }}>🗑</Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {open && (
        <div className="fixed inset-0 z-50 bg-black/40" onClick={() => setOpen(false)}>
          <div className="fixed inset-x-0 bottom-0 mx-auto max-h-[85vh] max-w-lg overflow-y-auto rounded-t-3xl bg-white p-5"
               onClick={(ei) => ei.stopPropagation()}>
            <h3 className="mb-3 text-lg font-bold">{t('exp.add')}</h3>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <Select label={t('exp.category')} value={form.category}
                        onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  {CATEGORIES.map((c) => <option key={c} value={c}>{t(`cat.${c}`)}</option>)}
                </Select>
                <Input label={t('exp.amount')} type="number" min="1" value={form.amount}
                       onChange={(e) => setForm({ ...form, amount: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Input label={t('exp.date')} type="date" value={form.date}
                       onChange={(e) => setForm({ ...form, date: e.target.value })} />
                <Select label={t('nav.crops')} value={form.crop_id}
                        onChange={(e) => setForm({ ...form, crop_id: e.target.value })}>
                  <option value="">—</option>
                  {cropOptions.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </Select>
              </div>
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <Input label={t('exp.note')} value={form.note}
                         onChange={(e) => setForm({ ...form, note: e.target.value })} />
                </div>
                {voice.supported && (
                  <button type="button"
                    onClick={() => (voice.listening ? voice.stop() : voice.start())}
                    className={`btn-tap rounded-xl px-4 py-2 ${voice.listening ? 'bg-red-600 text-white animate-pulse' : 'bg-green-100 text-green-800'}`}>
                    🎙
                  </button>
                )}
              </div>
              {voice.transcript && (
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  🎙 "{voice.transcript}" — {t('exp.voice')} (confirm before saving)
                </p>
              )}
              <div className="flex justify-end gap-2">
                <Button variant="ghost" onClick={() => setOpen(false)}>{t('common.cancel')}</Button>
                <Button onClick={save} disabled={!form.amount}>{t('common.save')}</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
