import { useApi } from '../hooks/useApi'
import { LANG_NAMES, Lang } from '../i18n/translations'
import { useAuth } from '../contexts/AuthContext'
import { useI18n } from '../contexts/I18nContext'
import { Badge, Card } from '../components/ui'
import type { IntegrationStatus } from '../types'

export default function Settings() {
  const { t } = useI18n()
  const { user } = useAuth()
  const { lang, setLang } = useI18n()
  const { data: services } = useApi<IntegrationStatus[]>('/integrations')

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-extrabold text-green-900">⚙️ {t('nav.settings')}</h1>

      <Card>
        <h3 className="mb-2 font-bold text-green-900">{t('set.language')}</h3>
        <div className="flex flex-wrap gap-2">
          {(Object.keys(LANG_NAMES) as Lang[]).map((l) => (
            <button key={l} onClick={() => setLang(l)}
              className={`btn-tap rounded-xl px-4 py-2 text-sm font-semibold ${
                lang === l ? 'bg-green-700 text-white' : 'bg-gray-100 text-gray-600'}`}>
              {LANG_NAMES[l]}
            </button>
          ))}
        </div>
      </Card>

      <Card>
        <h3 className="mb-2 font-bold text-green-900">{t('set.services')}</h3>
        <ul className="space-y-2 text-sm">
          {(services ?? []).map((s) => (
            <li key={s.name} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
              <div>
                <p className="font-semibold">{s.name}</p>
                <p className="text-xs text-gray-500">{s.detail}</p>
              </div>
              <Badge tone={s.live ? 'green' : 'amber'}>{s.live ? 'LIVE' : 'DEMO'}</Badge>
            </li>
          ))}
        </ul>
      </Card>

      {user?.is_demo && (
        <Card className="border-l-4 border-amber-400">
          <p className="text-sm text-gray-600">
            🎪 You are viewing the <b>demo farm</b>. Create an account to track your own fields.
          </p>
        </Card>
      )}
    </div>
  )
}
