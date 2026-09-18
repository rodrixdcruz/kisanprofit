import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { dict, Lang } from '../i18n/translations'
import { api } from '../lib/api'

interface I18nState {
  lang: Lang
  setLang: (l: Lang) => void
  t: (key: string) => string
}

const I18nContext = createContext<I18nState | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(
    () => (localStorage.getItem('kp_lang') as Lang) || 'en',
  )

  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  const setLang = (l: Lang) => {
    setLangState(l)
    localStorage.setItem('kp_lang', l)
    api.put('/auth/language', { language: l }).catch(() => { /* offline is fine */ })
  }

  const t = (key: string) => dict[lang][key] ?? dict.en[key] ?? key

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used inside I18nProvider')
  return ctx
}
