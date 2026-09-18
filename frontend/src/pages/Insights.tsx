import { useApi } from '../hooks/useApi'
import { useI18n } from '../contexts/I18nContext'
import { Card, EmptyState, Spinner } from '../components/ui'
import type { Insight } from '../types'

const ICONS = { info: 'ℹ️', good: '✅', warning: '⚠️' } as const

export default function Insights() {
  const { t } = useI18n()
  const { data, loading } = useApi<Insight[]>('/analytics/insights')

  if (loading) return <Spinner />
  const list = data ?? []

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold text-green-900">💡 {t('nav.insights')}</h1>
      {list.length === 0 ? <EmptyState message={t('common.empty')} /> : (
        <div className="space-y-3">
          {list.map((i, idx) => (
            <Card key={idx} className={`border-l-4 ${
              i.severity === 'warning' ? 'border-amber-400' :
              i.severity === 'good' ? 'border-green-500' : 'border-gray-300'}`}>
              <p className="font-bold text-gray-800">{ICONS[i.severity]} {i.title}</p>
              <p className="mt-1 text-sm text-gray-600">{i.detail}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
