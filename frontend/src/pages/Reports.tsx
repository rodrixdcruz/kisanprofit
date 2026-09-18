import { useApi } from '../hooks/useApi'
import { api } from '../lib/api'
import { useI18n } from '../contexts/I18nContext'
import { useToast } from '../contexts/ToastContext'
import { Button, Card, EmptyState, Spinner } from '../components/ui'
import type { CropProfit } from '../types'

export default function Reports() {
  const { t } = useI18n()
  const { push } = useToast()
  const { data: crops, loading } = useApi<CropProfit[]>('/analytics/crops')

  const dl = async (path: string, filename: string) => {
    try {
      await api.download(path, filename)
      push('success', t('common.download'))
    } catch (e) {
      push('error', e instanceof Error ? e.message : t('err.generic'))
    }
  }

  if (loading) return <Spinner />

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold text-green-900">📄 {t('nav.reports')}</h1>

      <Card>
        <h3 className="mb-2 font-bold text-green-900">{t('nav.crops')}</h3>
        {(crops ?? []).length === 0 ? <EmptyState message={t('common.empty')} /> : (
          <div className="flex flex-wrap gap-2">
            {(crops ?? []).map((c) => (
              <Button key={c.crop_id} variant="ghost"
                      onClick={() => dl(`/reports/crop/${c.crop_id}/pdf`, `${c.crop_name}_profitability.pdf`)}>
                📄 {c.crop_name} — {t('rep.cropPdf')}
              </Button>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <h3 className="mb-2 font-bold text-green-900">{t('nav.expenses')}</h3>
        <div className="flex flex-wrap gap-2">
          <Button variant="ghost" onClick={() => dl('/reports/expenses/pdf', 'expenses.pdf')}>
            {t('rep.expensesPdf')}
          </Button>
          <Button variant="ghost" onClick={() => dl('/reports/expenses/csv', 'expenses.csv')}>
            {t('rep.expensesCsv')}
          </Button>
        </div>
      </Card>

      <Card>
        <h3 className="mb-2 font-bold text-green-900">{t('nav.sales')}</h3>
        <Button variant="ghost" onClick={() => dl('/reports/sales/pdf', 'sales.pdf')}>
          {t('rep.salesPdf')}
        </Button>
      </Card>

      <Card>
        <h3 className="mb-2 font-bold text-green-900">{t('nav.reports')}</h3>
        <div className="flex flex-wrap gap-2">
          <Button variant="ghost" onClick={() => dl('/reports/monthly/pdf', 'monthly_summary.pdf')}>
            🗓 {t('rep.monthly')}
          </Button>
          <Button variant="ghost" onClick={() => dl('/reports/seasonal/pdf', 'seasonal_summary.pdf')}>
            🌦 {t('rep.seasonal')}
          </Button>
          <Button variant="ghost" onClick={() => dl('/reports/annual/pdf', 'annual_summary.pdf')}>
            📆 {t('rep.annual')}
          </Button>
        </div>
      </Card>
    </div>
  )
}
