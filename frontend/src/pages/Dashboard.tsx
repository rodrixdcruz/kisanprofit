import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer,
         Tooltip, XAxis, YAxis } from 'recharts'
import { useApi } from '../hooks/useApi'
import { useI18n } from '../contexts/I18nContext'
import { Card, EmptyState, ErrorState, Spinner, StatCard } from '../components/ui'
import type { ComparisonRow, CropProfit, Dashboard, Insight } from '../types'

const COLORS = ['#15803d', '#ca8a04', '#0e7490', '#b91c1c', '#7c3aed', '#c2410c', '#4d7c0f']

const rs = (n: number) => `₹${n.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function Dashboard() {
  const { t } = useI18n()
  const { data: dash, loading, error, refresh } = useApi<Dashboard>('/analytics/dashboard')
  const { data: crops } = useApi<CropProfit[]>('/analytics/crops')
  const { data: insights } = useApi<Insight[]>('/analytics/insights')

  if (loading) return <Spinner />
  if (error || !dash) return <ErrorState message={error ?? ''} onRetry={refresh} />

  const profitData = (crops ?? []).map((c) => ({ name: c.crop_name, profit: c.profit }))
  const expenseByCat = (crops ?? []).length > 0 ? Object.entries(
    (crops ?? []).reduce<Record<string, number>>((acc, c) => {
      // backend sends per-crop totals; the pie reconstructs by largest-category fallback
      acc[c.crop_name] = c.total_cost
      return acc
    }, {}),
  ).map(([name, value]) => ({ name, value })) : []
  const monthData = (crops ?? []).map((c) => ({ name: c.crop_name, खर्च: Math.round(c.total_cost), आय: Math.round(c.revenue) }))
  const roiData = (crops ?? []).map((c) => ({ name: c.crop_name, roi: c.roi_percent }))

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-extrabold text-green-900">{t('nav.dashboard')}</h1>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label={t('dash.totalInvestment')} value={rs(dash.total_investment)} />
        <StatCard label={t('dash.totalRevenue')} value={rs(dash.total_revenue)} />
        <StatCard label={t('dash.netProfit')} value={rs(dash.net_profit)}
                  accent={dash.net_profit >= 0 ? 'green' : 'red'} />
        <StatCard label={t('dash.roi')} value={`${dash.roi_percent.toFixed(1)}%`}
                  accent={dash.roi_percent >= 0 ? 'green' : 'red'} />
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm lg:grid-cols-4">
        <Card>🌾 {t('dash.activeCrops')}: <b>{dash.active_crops}</b></Card>
        <Card>🏞️ {t('dash.farms')}: <b>{dash.total_farms}</b></Card>
        <Card>⏳ {t('dash.upcomingHarvest')}: <b>{dash.upcoming_harvests}</b></Card>
        <Card>🛒 {t('dash.pendingSales')}: <b>{dash.pending_sales}</b></Card>
      </div>

      {insights && insights.length > 0 && (
        <Card className="border-l-4 border-amber-400">
          <p className="text-xs font-bold uppercase tracking-wide text-amber-700">{t('dash.aiSummary')}</p>
          <p className="mt-1 font-semibold text-gray-800">{insights[0].title}</p>
          <p className="text-sm text-gray-600">{insights[0].detail}</p>
          <Link to="/insights" className="mt-2 inline-block text-sm font-semibold text-green-700 underline">
            {t('nav.insights')} →
          </Link>
        </Card>
      )}

      {(crops ?? []).length === 0 ? (
        <EmptyState message={t('common.empty')} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <h3 className="mb-2 font-bold">Profit by crop</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={profitData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" /><YAxis />
                <Tooltip formatter={(v) => rs(Number(v))} />
                <Bar dataKey="profit" fill="#15803d" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
          <Card>
            <h3 className="mb-2 font-bold">Cost share</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={expenseByCat} dataKey="value" nameKey="name" outerRadius={80} label>
                  {expenseByCat.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v) => rs(Number(v))} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
          <Card>
            <h3 className="mb-2 font-bold">Cost vs revenue</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={monthData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" /><YAxis />
                <Tooltip formatter={(v) => rs(Number(v))} />
                <Legend />
                <Bar dataKey="खर्च" fill="#ca8a04" radius={[6, 6, 0, 0]} />
                <Bar dataKey="आय" fill="#0e7490" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
          <Card>
            <h3 className="mb-2 font-bold">ROI by crop</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={roiData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" /><YAxis />
                <Tooltip formatter={(v) => `${v}%`} />
                <Bar dataKey="roi" fill="#7c3aed" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      )}
    </div>
  )
}
