import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { useI18n } from '../contexts/I18nContext'
import { useVoice } from '../hooks/useVoice'
import { Card } from '../components/ui'

interface Msg { role: 'user' | 'ai'; text: string; provider?: string }

const SUGGESTIONS = [
  'Where am I spending the most?',
  'What is my profit per crop?',
  'Which crop does best?',
]

export default function AIChat() {
  const { t, lang } = useI18n()
  const voice = useVoice(lang === 'hi' ? 'hi-IN' : lang === 'mr' ? 'mr-IN' : 'en-IN')
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (voice.transcript) setInput(voice.transcript)
  }, [voice.transcript])

  const send = async (text?: string) => {
    const q = (text ?? input).trim()
    if (!q || busy) return
    setMessages((m) => [...m, { role: 'user', text: q }])
    setInput('')
    setBusy(true)
    try {
      const res = await api.post<{ answer: string; provider: string }>('/ai/chat', { message: q })
      setMessages((m) => [...m, { role: 'ai', text: res.answer, provider: res.provider }])
    } catch (e) {
      setMessages((m) => [...m, { role: 'ai', text: e instanceof Error ? e.message : t('err.generic') }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-9rem)] flex-col">
      <h1 className="mb-3 text-2xl font-extrabold text-green-900">🤖 {t('nav.ai')}</h1>

      <Card className="mb-3 border-l-4 border-green-600 text-sm text-gray-600">
        🔒 {t('ai.disclaimer')}
      </Card>

      <div className="flex-1 space-y-3 overflow-y-auto rounded-2xl bg-white p-4 shadow-sm ring-1 ring-black/5">
        {messages.length === 0 && (
          <div className="space-y-2 py-6 text-center">
            <div className="text-4xl">🤖🌾</div>
            <p className="text-sm text-gray-500">{t('ai.ask')}</p>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)}
                  className="rounded-full border border-green-200 px-3 py-1.5 text-sm text-green-800 hover:bg-green-50">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm ${
              m.role === 'user' ? 'bg-green-700 text-white' : 'bg-gray-100 text-gray-800'}`}>
              {m.text}
              {m.provider && (
                <span className="mt-1 block text-[10px] uppercase tracking-wide text-gray-400">
                  {m.provider}
                </span>
              )}
            </div>
          </div>
        ))}
        {busy && <p className="animate-pulse text-sm text-gray-400">{t('ai.think')}…</p>}
        <div ref={endRef} />
      </div>

      <div className="mt-3 flex items-center gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)}
               onKeyDown={(e) => e.key === 'Enter' && send()}
               placeholder={t('ai.ask')}
               className="btn-tap flex-1 rounded-xl border border-gray-300 px-4 outline-none focus:border-green-600" />
        {voice.supported && (
          <button type="button" onClick={() => (voice.listening ? voice.stop() : voice.start())}
            className={`btn-tap rounded-xl px-4 ${voice.listening ? 'animate-pulse bg-red-600 text-white' : 'bg-green-100'}`}>
            🎙
          </button>
        )}
        <button onClick={() => send()} disabled={busy || !input.trim()}
          className="btn-tap rounded-xl bg-green-700 px-5 font-semibold text-white disabled:opacity-50">
          ➤
        </button>
      </div>
    </div>
  )
}
