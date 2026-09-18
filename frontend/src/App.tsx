import { NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { LANG_NAMES, Lang } from './i18n/translations'
import { useI18n } from './contexts/I18nContext'

import Landing from './pages/Landing'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Farms from './pages/Farms'
import Crops from './pages/Crops'
import Expenses from './pages/Expenses'
import Production from './pages/Production'
import Sales from './pages/Sales'
import Simulator from './pages/Simulator'
import Compare from './pages/Compare'
import AIChat from './pages/AIChat'
import Insights from './pages/Insights'
import Weather from './pages/Weather'
import Market from './pages/Market'
import Reports from './pages/Reports'
import Notifications from './pages/Notifications'
import Settings from './pages/Settings'

const NAV = [
  { to: '/dashboard', key: 'nav.dashboard', icon: '🏠' },
  { to: '/farms', key: 'nav.farms', icon: '🏞️' },
  { to: '/crops', key: 'nav.crops', icon: '🌾' },
  { to: '/expenses', key: 'nav.expenses', icon: '🧾' },
  { to: '/production', key: 'nav.production', icon: '🌾' },
  { to: '/sales', key: 'nav.sales', icon: '💰' },
  { to: '/simulator', key: 'nav.simulator', icon: '📈' },
  { to: '/compare', key: 'nav.compare', icon: '⚖️' },
  { to: '/ai', key: 'nav.ai', icon: '🤖' },
  { to: '/insights', key: 'nav.insights', icon: '💡' },
  { to: '/weather', key: 'nav.weather', icon: '🌦️' },
  { to: '/market', key: 'nav.market', icon: '🏪' },
  { to: '/reports', key: 'nav.reports', icon: '📄' },
  { to: '/notifications', key: 'nav.notifications', icon: '🔔' },
  { to: '/settings', key: 'nav.settings', icon: '⚙️' },
]

const MOBILE_NAV = NAV.filter((n) =>
  ['/dashboard', '/expenses', '/ai', '/market', '/settings'].includes(n.to))

function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const { lang, setLang, t } = useI18n()
  const navigate = useNavigate()
  return (
    <div className="flex min-h-screen bg-[#f6f7f2]">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-56 shrink-0 flex-col overflow-y-auto border-r bg-white p-3 md:flex">
        <div className="px-2 py-3 text-xl font-extrabold text-green-800">🌾 {t('app.name')}</div>
        <nav className="flex-1 space-y-0.5">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${isActive ? 'bg-green-100 font-semibold text-green-900' : 'text-gray-600 hover:bg-green-50'}`}>
              <span>{n.icon}</span>{t(n.key)}
            </NavLink>
          ))}
        </nav>
        <select aria-label="Language" value={lang} onChange={(e) => setLang(e.target.value as Lang)}
                className="mb-2 w-full rounded-lg border px-2 py-1.5 text-sm">
          {(Object.keys(LANG_NAMES) as Lang[]).map((l) => (
            <option key={l} value={l}>{LANG_NAMES[l]}</option>
          ))}
        </select>
        <button onClick={() => { logout(); navigate('/login') }}
                className="rounded-lg px-3 py-2 text-left text-sm text-gray-500 hover:bg-red-50">
          ⎋ Log out
        </button>
      </aside>

      {/* Mobile top bar */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-40 flex items-center justify-between bg-green-800 px-4 py-3 text-white md:hidden">
          <span className="font-bold">🌾 {t('app.name')}</span>
          <button onClick={() => { logout(); navigate('/login') }} className="text-sm">Log out</button>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-5 pb-24 md:pb-8">{children}</main>
        {/* Mobile bottom nav */}
        <nav className="fixed inset-x-0 bottom-0 z-40 flex justify-around border-t bg-white py-1.5 md:hidden">
          {MOBILE_NAV.map((n) => (
            <NavLink key={n.to} to={n.to}
              className={({ isActive }) =>
                `flex flex-col items-center px-3 py-1 text-[11px] ${isActive ? 'text-green-800 font-semibold' : 'text-gray-500'}`}>
              <span className="text-xl">{n.icon}</span>{t(n.key)}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  )
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

export default function App() {
  const { token } = useAuth()
  return (
    <Routes>
      <Route path="/" element={token ? <Navigate to="/dashboard" /> : <Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
      <Route path="/farms" element={<RequireAuth><Farms /></RequireAuth>} />
      <Route path="/crops" element={<RequireAuth><Crops /></RequireAuth>} />
      <Route path="/expenses" element={<RequireAuth><Expenses /></RequireAuth>} />
      <Route path="/production" element={<RequireAuth><Production /></RequireAuth>} />
      <Route path="/sales" element={<RequireAuth><Sales /></RequireAuth>} />
      <Route path="/simulator" element={<RequireAuth><Simulator /></RequireAuth>} />
      <Route path="/compare" element={<RequireAuth><Compare /></RequireAuth>} />
      <Route path="/ai" element={<RequireAuth><AIChat /></RequireAuth>} />
      <Route path="/insights" element={<RequireAuth><Insights /></RequireAuth>} />
      <Route path="/weather" element={<RequireAuth><Weather /></RequireAuth>} />
      <Route path="/market" element={<RequireAuth><Market /></RequireAuth>} />
      <Route path="/reports" element={<RequireAuth><Reports /></RequireAuth>} />
      <Route path="/notifications" element={<RequireAuth><Notifications /></RequireAuth>} />
      <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
