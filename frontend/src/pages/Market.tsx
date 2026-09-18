import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { useI18n } from '../contexts/I18nContext'
import { Badge, Card, Input, Spinner } from '../components/ui'
import type { MarketResponse } from '../types'

const rs = (n: number | null) => (n == null ? '—' : `₹${n.toLocaleString('en-IN')}`)

export default function Market() {
  const { t } = useI18n()
  const [commodity, setCommodity] = useState('')
  const { data, loading } = useApi<MarketResponse>(`/market${commodity ? `?commodity=${commodity}` : ''}`)
  const [simPrice, setSimPrice] = useState('')
  const [simQty, setSimQty] = useState('')

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold text-green-900">🏪 {t('market.title')}</h1>

      <Card>
        <Input placeholder="Filter commodity (e.g. cotton)" value={commodity}
               onChange={(e) => setCommodity(e.target.value)} />
      </Card>

      {data && (
        <Card className="border-l-4 border-gray-300">
          <Badge tone={data.live ? 'green' : 'amber'}>
            {data.live ? t('market.liveNote') : t('market.referenceNote')}
          </Badge>
          {data.note && <p className="mt-1 text-xs text-gray-500">{data.note}</p>}
        </Card>
      )}

      {loading ? <Spinner /> : (
        <Card className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b text-xs uppercase tracking-wide text-gray-400">
                <th className="py-2 pr-4">Commodity</th>
                <th className="py-2 pr-4">Market</th>
                <th className="py-2 pr-4">Min</th>
                <th className="py-2 pr-4">Modal</th>
                <th className="py-2 pr-4">Max</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {(data?.rows ?? []).map((r, i) => (
                <tr key={i} className="border-b last:border-0">
                  <td className="py-2 pr-4 font-semibold">{r.commodity}</td>
                  <td className="py-2 pr-4 text-gray-500">{r.market || '—'}</td>
                  <td className="py-2 pr-4">{rs(r.min_price)}</td>
                  <td className="py-2 pr-4 font-bold text-green-800">{rs(r.modal_price)}</td>
                  <td className="py-2 pr-4">{rs(r.max_price)}</td>
                  <td className="text-xs text-gray-400">{r.price_date ?? ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <Card>
        <p className="mb-2 text-sm font-semibold text-gray-600">{t('market.simulator')}</p>
        <div className="grid grid-cols-2 gap-2 sm:max-w-sm">
          <Input type="number" placeholder="Price ₹/q" value={simPrice}
                 onChange={(e) => setSimPrice(e.target.value)} />
          <Input type="number" placeholder="Quantity q" value={simQty}
                 onChange={(e) => setSimQty(e.target.value)} />
        </div>
        {Number(simPrice) > 0 && Number(simQty) > 0 && (
          <p className="mt-2 text-lg font-bold text-green-700">
            {rs(Number(simPrice) * Number(simQty))}
          </p>
        )}
      </Card>
    </div>
  )
}
