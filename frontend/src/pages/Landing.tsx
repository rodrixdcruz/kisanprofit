import { Link } from 'react-router-dom'
import { useI18n } from '../contexts/I18nContext'

export default function Landing() {
  const { t } = useI18n()
  return (
    <div className="min-h-screen bg-gradient-to-b from-green-800 to-green-950 text-white">
      <header className="mx-auto flex max-w-5xl items-center justify-between px-5 py-5">
        <span className="text-xl font-extrabold">🌾 {t('app.name')}</span>
        <Link to="/login" className="rounded-xl bg-white px-4 py-2 font-semibold text-green-900">
          {t('auth.login')}
        </Link>
      </header>
      <section className="mx-auto max-w-5xl px-5 pb-16 pt-10 text-center">
        <h1 className="text-4xl font-extrabold leading-tight md:text-5xl">{t('app.tagline')}</h1>
        <p className="mx-auto mt-4 max-w-2xl text-green-100">
          Track every rupee across farms and crops, see real profit per crop, simulate prices
          before you sell, and ask AI about your own records — in English, हिन्दी or मराठी.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to="/login" className="btn-tap rounded-xl bg-amber-400 px-6 py-3 text-lg font-bold text-green-950">
            {t('auth.register')} →
          </Link>
          <Link to="/login" className="btn-tap rounded-xl border border-white/40 px-6 py-3 text-lg font-semibold">
            {t('auth.demo')}
          </Link>
        </div>
        <div className="mt-14 grid gap-4 text-left sm:grid-cols-2 lg:grid-cols-3">
          {[
            ['🧾', '10-second expense entry', 'Voice input, quick-add buttons, 12 categories.'],
            ['📈', 'Real profit per crop', 'Costs, revenue, ROI, break-even — computed server-side.'],
            ['🤖', 'AI on your own data', 'Answers only from your records; never invents numbers.'],
            ['🌦️', 'Weather advisories', 'Live 7-day forecast with farming tips, keyless.'],
            ['🏪', 'Mandi prices', 'Daily prices with sell recommendations.'],
            ['📄', 'PDF & CSV reports', 'Crop profitability, seasonal summaries, exports.'],
          ].map(([icon, title, body]) => (
            <div key={title} className="rounded-2xl bg-white/10 p-5 ring-1 ring-white/15">
              <div className="text-3xl">{icon}</div>
              <h3 className="mt-2 font-bold">{title}</h3>
              <p className="mt-1 text-sm text-green-100">{body}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
