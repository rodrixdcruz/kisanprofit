import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { useI18n } from '../contexts/I18nContext'
import { Card, EmptyState, ErrorState, Spinner } from '../components/ui'
import type { Farm, Weather } from '../types'

const CODE_ICON: Record<number, string> = {
  0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️', 45: '🌫️', 48: '🌫️',
  51: '🌦️', 53: '🌦️', 55: '🌧️', 61: '🌧️', 63: '🌧️', 65: '⛈️',
  66: '🌧️', 67: '🌧️', 71: '🌨️', 73: '🌨️', 75: '❄️',
  80: '🌦️', 81: '🌧️', 82: '⛈️', 95: '⛈️', 96: '⛈️', 99: '⛈️',
}

export default function Weather() {
  const { t } = useI18n()
  const { data: farms } = useApi<Farm[]>('/farms')
  const withLoc = (farms ?? []).filter((f) => f.latitude != null && f.longitude != null)
  const [farmId, setFarmId] = useState<number | null>(null)
  const farm = withLoc.find((f) => f.id === (farmId ?? withLoc[0]?.id))
  const { data, loading, error } = useApi<Weather>(
    farm ? `/weather?latitude=${farm.latitude}&longitude=${farm.longitude}` : null)

  if ((farms ?? []).length === 0) return <EmptyState icon="🏞️" message={t('common.empty')} />
  if (withLoc.length === 0) return <EmptyState icon="🗺️" message="Add a farm location on the map to see weather." />
  if (loading) return <Spinner />
  if (error) return <ErrorState message={error} />

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-extrabold text-green-900">🌦️ {t('weather.title')}</h1>
        <select value={farm?.id} onChange={(e) => setFarmId(Number(e.target.value))}
                className="rounded-lg border px-2 py-1.5 text-sm">
          {withLoc.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
        </select>
      </div>

      {data?.advisory && (
        <Card className="border-l-4 border-amber-400">
          <p className="mb-1 text-xs font-bold uppercase tracking-wide text-amber-700">{t('weather.advisory')}</p>
          <ul className="list-inside list-disc space-y-1 text-sm text-gray-700">
            {data.advisory.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </Card>
      )}

      {data && data.days.length === 0 && <EmptyState icon="📡" message={data.advisory[0] ?? t('err.network')} />}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
        {(data?.days ?? []).map((d) => (
          <Card key={d.date} className="text-center">
            <p className="text-xs font-semibold text-gray-500">
              {new Date(d.date).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}
            </p>
            <div className="my-1 text-3xl">{CODE_ICON[d.weather_code] ?? '🌡️'}</div>
            <p className="text-sm font-bold">{Math.round(d.temp_max_c)}° <span className="font-normal text-gray-400">{Math.round(d.temp_min_c)}°</span></p>
            <p className="text-xs text-cyan-700">💧 {d.precipitation_mm} mm</p>
            <p className="text-xs text-gray-400">{d.precipitation_probability_percent}%</p>
          </Card>
        ))}
      </div>

      {data?.cached && <p className="text-xs text-gray-400">cached forecast</p>}
    </div>
  )
}
