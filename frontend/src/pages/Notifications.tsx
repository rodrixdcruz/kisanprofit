import { useApi } from '../hooks/useApi'
import { api } from '../lib/api'
import { useI18n } from '../contexts/I18nContext'
import { Button, Card, EmptyState, Spinner } from '../components/ui'
import type { Notification } from '../types'

const ICONS: Record<string, string> = { harvest_due: '🌾', high_expense: '💸', system: '📣' }

export default function Notifications() {
  const { t } = useI18n()
  const { data, loading, refresh } = useApi<Notification[]>('/notifications')

  const markAll = async () => {
    await api.post('/notifications/read-all')
    refresh()
  }
  const markOne = async (id: number) => {
    await api.post(`/notifications/${id}/read`)
    refresh()
  }

  if (loading) return <Spinner />
  const list = data ?? []
  const unread = list.filter((n) => !n.read_at).length

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-extrabold text-green-900">🔔 {t('notif.title')}</h1>
        {unread > 0 && <Button variant="ghost" onClick={markAll}>{t('notif.markAll')} ({unread})</Button>}
      </div>
      {list.length === 0 ? <EmptyState icon="🔔" message={t('notif.empty')} /> : (
        <div className="space-y-2">
          {list.map((n) => (
            <Card key={n.id} className={n.read_at ? 'opacity-60' : 'border-l-4 border-amber-400'}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-gray-800">{ICONS[n.kind] ?? '🔔'} {n.title}</p>
                  {n.body && <p className="mt-0.5 text-sm text-gray-600">{n.body}</p>}
                  <p className="mt-1 text-xs text-gray-400">{new Date(n.created_at).toLocaleString()}</p>
                </div>
                {!n.read_at && (
                  <button onClick={() => markOne(n.id)}
                          className="rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-800">
                    ✓
                  </button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
