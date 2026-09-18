import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../lib/api'
import { useI18n } from '../contexts/I18nContext'
import { useToast } from '../contexts/ToastContext'
import { Button, Card, EmptyState, ErrorState, Input, Modal, Spinner } from '../components/ui'
import MapPicker from '../components/MapPicker'
import type { Farm } from '../types'

export default function Farms() {
  const { t } = useI18n()
  const { data, loading, error, refresh } = useApi<Farm[]>('/farms')
  const { push } = useToast()
  const [editing, setEditing] = useState<Farm | null>(null)
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ name: '', area_acres: '1', village: '', latitude: '', longitude: '' })

  const openNew = () => {
    setEditing(null)
    setForm({ name: '', area_acres: '1', village: '', latitude: '', longitude: '' })
    setOpen(true)
  }
  const openEdit = (f: Farm) => {
    setEditing(f)
    setForm({
      name: f.name, area_acres: String(f.area_acres), village: f.village ?? '',
      latitude: f.latitude?.toString() ?? '', longitude: f.longitude?.toString() ?? '',
    })
    setOpen(true)
  }

  const save = async () => {
    const payload = {
      name: form.name,
      area_acres: Number(form.area_acres),
      village: form.village || null,
      latitude: form.latitude ? Number(form.latitude) : null,
      longitude: form.longitude ? Number(form.longitude) : null,
    }
    try {
      if (editing) await api.put(`/farms/${editing.id}`, payload)
      else await api.post('/farms', payload)
      setOpen(false)
      refresh()
      push('success', t('common.save'))
    } catch (e) {
      push('error', e instanceof Error ? e.message : t('err.generic'))
    }
  }

  const remove = async (id: number) => {
    if (!confirm('Delete this farm and all its crops?')) return
    await api.delete(`/farms/${id}`)
    refresh()
  }

  if (loading) return <Spinner />
  if (error) return <ErrorState message={error} onRetry={refresh} />

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-extrabold text-green-900">{t('nav.farms')}</h1>
        <Button onClick={openNew}>＋ {t('farms.add')}</Button>
      </div>

      {(data ?? []).length === 0 ? <EmptyState icon="🏞️" message={t('common.empty')} /> : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {(data ?? []).map((f) => (
            <Card key={f.id}>
              <div className="flex items-start justify-between">
                <h3 className="font-bold text-green-900">{f.name}</h3>
                <span className="text-xs text-gray-400">#{f.id}</span>
              </div>
              <p className="mt-1 text-sm text-gray-600">{f.area_acres} {t('farms.area')}</p>
              {f.village && <p className="text-sm text-gray-500">📍 {f.village}</p>}
              <div className="mt-3 flex gap-2">
                <Button variant="ghost" onClick={() => openEdit(f)}>{t('common.edit')}</Button>
                <Button variant="danger" onClick={() => remove(f.id)}>{t('common.delete')}</Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={open} onClose={() => setOpen(false)} title={editing ? t('common.edit') : t('farms.add')}>
        <div className="space-y-3">
          <Input label={t('farms.add')} value={form.name}
                 onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label={t('farms.area')} type="number" step="0.1" min="0.1" value={form.area_acres}
                 onChange={(e) => setForm({ ...form, area_acres: e.target.value })} />
          <Input label={t('farms.village')} value={form.village}
                 onChange={(e) => setForm({ ...form, village: e.target.value })} />
          <MapPicker
            latitude={form.latitude ? Number(form.latitude) : null}
            longitude={form.longitude ? Number(form.longitude) : null}
            onChange={(lat, lon) => setForm({ ...form, latitude: String(lat), longitude: String(lon) })} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setOpen(false)}>{t('common.cancel')}</Button>
            <Button onClick={save} disabled={!form.name}>{t('common.save')}</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
