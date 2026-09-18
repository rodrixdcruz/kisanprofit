import { useApi } from '../hooks/useApi'
import { useI18n } from '../contexts/I18nContext'
import { Badge, Card, EmptyState, Spinner } from '../components/ui'
import type { ComparisonRow } from '../types'

const rs = (n: number) => `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function Compare() {
  const { t } = useI18n()
  const { data, loading } = useApi<ComparisonRow[]>('/analytics/comparison')

  if (loading) return <Spinner />
  if (!data || data.length === 0) return <EmptyState icon="⚖️" message={t('common.empty')} />

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold text-green-900">{t('cmp.title')}</h1>
      <Card className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b text-xs uppercase tracking-wide text-gray-400">
              <th className="py-2 pr-4">{t('nav.crops')}</th>
              <th className="py-2 pr-4">{t('dash.netProfit')}</th>
              <th className="py-2 pr-4">{t('dash.roi')}</th>
              <th className="py-2 pr-4">{t('dash.netProfit')} / acre</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.map((r) => (
              <tr key={r.crop_name} className={`border-b last:border-0 ${r.is_best ? 'bg-green-50' : ''}`}>
                <td className="py-2.5 pr-4 font-semibold">{r.crop_name}</td>
                <td className="py-2.5 pr-4">{rs(r.profit)}</td>
                <td className="py-2.5 pr-4">{r.roi_percent.toFixed(0)}%</td>
                <td className="py-2.5 pr-4">{rs(r.profit_per_acre)}</td>
                <td>{r.is_best && <Badge tone="green">🏆 {t('cmp.best')}</Badge>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
