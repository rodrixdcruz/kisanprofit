import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { LANG_NAMES, Lang } from '../i18n/translations'
import { useI18n } from '../contexts/I18nContext'
import { Button, Input } from '../components/ui'

export default function Login() {
  const { login, register, demoLogin } = useAuth()
  const { lang, setLang, t } = useI18n()
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [name, setName] = useState('')
  const [mobile, setMobile] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (mode === 'login') await login(mobile, password)
      else await register(name, mobile, password, lang)
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : t('err.generic'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-green-800 to-green-950 p-4">
      <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
        <div className="mb-5 text-center">
          <div className="text-4xl">🌾</div>
          <h1 className="mt-1 text-2xl font-extrabold text-green-900">{t('app.name')}</h1>
          <p className="text-sm text-gray-500">{t('app.tagline')}</p>
        </div>

        <div className="mb-4 flex justify-center gap-2">
          {(Object.keys(LANG_NAMES) as Lang[]).map((l) => (
            <button key={l} type="button" onClick={() => setLang(l)}
              className={`rounded-full px-3 py-1 text-sm ${lang === l ? 'bg-green-700 text-white' : 'bg-gray-100 text-gray-600'}`}>
              {LANG_NAMES[l]}
            </button>
          ))}
        </div>

        <div className="mb-4 grid grid-cols-2 rounded-xl bg-gray-100 p-1 text-sm font-semibold">
          <button type="button" onClick={() => setMode('login')}
            className={`rounded-lg py-2 ${mode === 'login' ? 'bg-white shadow' : 'text-gray-500'}`}>
            {t('auth.login')}
          </button>
          <button type="button" onClick={() => setMode('register')}
            className={`rounded-lg py-2 ${mode === 'register' ? 'bg-white shadow' : 'text-gray-500'}`}>
            {t('auth.register')}
          </button>
        </div>

        <form onSubmit={submit} className="space-y-3">
          {mode === 'register' && (
            <Input label={t('auth.name')} value={name} onChange={(e) => setName(e.target.value)}
                   required minLength={2} autoComplete="name" />
          )}
          <Input label={t('auth.mobile')} value={mobile} onChange={(e) => setMobile(e.target.value)}
                 required inputMode="numeric" pattern="[0-9]{10}" maxLength={15}
                 placeholder="9999999999" autoComplete="tel" />
          <Input label={t('auth.password')} type="password" value={password}
                 onChange={(e) => setPassword(e.target.value)} required minLength={6}
                 autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? '…' : mode === 'login' ? t('auth.login') : t('auth.register')}
          </Button>
        </form>

        <div className="my-4 flex items-center gap-3 text-xs text-gray-400">
          <span className="h-px flex-1 bg-gray-200" />{t('auth.noAccount')}<span className="h-px flex-1 bg-gray-200" />
        </div>
        <Button variant="ghost" className="w-full"
                onClick={async () => { await demoLogin(); navigate('/dashboard') }}>
          🎪 {t('auth.demo')}
        </Button>
      </div>
    </div>
  )
}
