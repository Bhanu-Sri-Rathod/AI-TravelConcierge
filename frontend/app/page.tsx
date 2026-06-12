'use client'
import { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import dynamic from 'next/dynamic'
import { 
  Send, Plane, Cloud, Map, DollarSign, LogOut, 
  Bookmark, History, Mic, MicOff, ChevronRight,
  Globe, Wind, Thermometer, Calendar
} from 'lucide-react'
import { login, register, setToken, setUser, getToken, getUser, clearToken, streamChat, apiFetch } from '../lib/api'

const MapView = dynamic(() => import('../components/MapView'), { ssr: false })

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  intent?: string
  apiData?: Record<string, unknown>
  loading?: boolean
}

const SUGGESTIONS = [
  { icon: <Plane size={14}/>, text: "Flights from DEL to DXB tomorrow" },
  { icon: <Cloud size={14}/>, text: "Weather in Paris next week" },
  { icon: <Map size={14}/>, text: "Plan a 5-day trip to Tokyo" },
  { icon: <DollarSign size={14}/>, text: "Convert 10000 INR to EUR" },
  { icon: <Globe size={14}/>, text: "Best time to visit Bali" },
  { icon: <Calendar size={14}/>, text: "3-day itinerary for Dubai" },
]

const INTENT_COLORS: Record<string, string> = {
  flights: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  weather: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
  itinerary: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  currency: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  general: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
}

const INTENT_ICONS: Record<string, JSX.Element> = {
  flights: <Plane size={11}/>,
  weather: <Cloud size={11}/>,
  itinerary: <Map size={11}/>,
  currency: <DollarSign size={11}/>,
  general: <Globe size={11}/>,
}

export default function Home() {
  const [authed, setAuthed]   = useState(false)
  const [authMode, setAuthMode] = useState<'login'|'register'>('login')
  const [email, setEmail]     = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [authErr, setAuthErr] = useState('')
  const [user, setUserState]  = useState<{username: string}|null>(null)

  const [messages, setMessages] = useState<Message[]>([{
    id: '0', role: 'assistant',
    content: "## Welcome to AI Travel Concierge ✈️\n\nI can help you with:\n- **Flight search** between any airports\n- **Weather forecasts** for your destination\n- **Day-by-day itineraries** with local tips\n- **Currency conversion** for travel budgeting\n\nWhat are you planning?",
  }])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)
  const [mapData, setMapData] = useState<{lat: number; lon: number; name: string} | null>(null)
  const [trips, setTrips]     = useState<Record<string, unknown>[]>([])
  const [showTrips, setShowTrips] = useState(false)
  const [listening, setListening] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)

  useEffect(() => {
    const token = getToken()
    const u = getUser()
    if (token && u) { setAuthed(true); setUserState(u); loadTrips() }
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadTrips = async () => {
    try {
      const data = await apiFetch('/chat/trips')
      setTrips(data)
    } catch {}
  }

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setAuthErr('')
    try {
      let data
      if (authMode === 'login') {
        data = await login(email, password)
      } else {
        data = await register(email, username, password)
      }
      setToken(data.access_token)
      const u = { username: data.username }
      setUser(u); setUserState(u); setAuthed(true)
      loadTrips()
    } catch (err: unknown) {
      setAuthErr(err instanceof Error ? err.message : 'Error')
    }
  }

  const handleLogout = () => {
    clearToken(); localStorage.removeItem('tc_user')
    setAuthed(false); setUserState(null); setTrips([])
  }

  const send = useCallback(async (text?: string) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    setLoading(true)

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: msg }
    const assistantId = (Date.now() + 1).toString()
    const loadingMsg: Message = { id: assistantId, role: 'assistant', content: '', loading: true }
    
    setMessages(prev => [...prev, userMsg, loadingMsg])

    const history = messages.slice(-8).map(m => ({ role: m.role, content: m.content }))

    try {
      let fullText = ''
      let intent = 'general'
      let apiData: Record<string, unknown> = {}

      for await (const chunk of streamChat(msg, history)) {
        if (chunk.type === 'text') {
          fullText += chunk.content
          setMessages(prev => prev.map(m => 
            m.id === assistantId ? { ...m, content: fullText, loading: false } : m
          ))
        } else if (chunk.type === 'meta') {
          intent = chunk.intent
        } else if (chunk.type === 'api_data') {
          apiData = chunk.data
          // Update map if location data available
          const loc = (apiData.location as Record<string,unknown>) || (apiData as Record<string,unknown>)
          if (loc?.latitude && loc?.longitude) {
            setMapData({ 
              lat: loc.latitude as number, 
              lon: loc.longitude as number, 
              name: (loc.name as string || (apiData.city as string) || msg)
            })
          } else if ((apiData as {city?: string; latitude?: number; longitude?: number}).latitude) {
            setMapData({ 
              lat: (apiData as {latitude: number}).latitude, 
              lon: (apiData as {longitude: number}).longitude, 
              name: (apiData as {city?: string}).city || msg 
            })
          }
        } else if (chunk.type === 'done') {
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? { ...m, content: fullText, loading: false, intent, apiData } : m
          ))
        } else if (chunk.type === 'error') {
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? { ...m, content: `Error: ${chunk.content}`, loading: false } : m
          ))
        }
      }
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m.id === assistantId 
          ? { ...m, content: 'Connection error. Make sure the backend is running on port 8000.', loading: false }
          : m
      ))
    }
    setLoading(false)
  }, [input, loading, messages])

  const startVoice = () => {
    const SR = (window as unknown as {SpeechRecognition?: SpeechRecognition; webkitSpeechRecognition?: SpeechRecognition}).SpeechRecognition 
            || (window as unknown as {webkitSpeechRecognition?: SpeechRecognition}).webkitSpeechRecognition
    if (!SR) return alert('Voice not supported in this browser')
    const recognition = new SR()
    recognition.lang = 'en-IN'
    recognition.onresult = (e: SpeechRecognitionEvent) => setInput(e.results[0][0].transcript)
    recognition.onend = () => setListening(false)
    recognitionRef.current = recognition
    setListening(true)
    recognition.start()
  }

  const stopVoice = () => {
    recognitionRef.current?.stop()
    setListening(false)
  }

  const saveCurrentTrip = async () => {
    const lastItinerary = [...messages].reverse().find(m => m.intent === 'itinerary')
    if (!lastItinerary) return alert('No itinerary to save yet!')
    const dest = prompt('Trip name?', 'My Trip')
    if (!dest) return
    try {
      await apiFetch('/chat/trips', {
        method: 'POST',
        body: JSON.stringify({ title: dest, destination: dest, itinerary: { content: lastItinerary.content } })
      })
      loadTrips()
      alert('Trip saved!')
    } catch {}
  }

  if (!authed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="text-4xl mb-2">✈️</div>
            <h1 className="text-2xl font-bold text-white">AI Travel Concierge</h1>
            <p className="text-slate-400 text-sm mt-1">Your intelligent travel planning assistant</p>
          </div>
          <form onSubmit={handleAuth} className="bg-slate-800 rounded-2xl p-6 space-y-4 border border-slate-700">
            <h2 className="text-lg font-semibold text-white">
              {authMode === 'login' ? 'Sign in' : 'Create account'}
            </h2>
            <input
              type="email" placeholder="Email" value={email}
              onChange={e => setEmail(e.target.value)} required
              className="w-full bg-slate-700 text-white rounded-xl px-4 py-3 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
            {authMode === 'register' && (
              <input
                type="text" placeholder="Username" value={username}
                onChange={e => setUsername(e.target.value)} required
                className="w-full bg-slate-700 text-white rounded-xl px-4 py-3 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
              />
            )}
            <input
              type="password" placeholder="Password" value={password}
              onChange={e => setPassword(e.target.value)} required
              className="w-full bg-slate-700 text-white rounded-xl px-4 py-3 text-sm border border-slate-600 focus:border-blue-500 focus:outline-none"
            />
            {authErr && <p className="text-red-400 text-xs">{authErr}</p>}
            <button type="submit" className="w-full bg-blue-600 hover:bg-blue-500 text-white rounded-xl py-3 font-medium transition-colors">
              {authMode === 'login' ? 'Sign in' : 'Register'}
            </button>
            <p className="text-center text-sm text-slate-400">
              {authMode === 'login' ? "Don't have an account? " : "Already have an account? "}
              <button type="button" onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
                className="text-blue-400 hover:text-blue-300">
                {authMode === 'login' ? 'Register' : 'Sign in'}
              </button>
            </p>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-xl">✈️</span>
          <div>
            <h1 className="font-semibold text-white text-sm">AI Travel Concierge</h1>
            <p className="text-xs text-slate-400">Powered by Gemini + LangGraph</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 hidden sm:block">Hi, {user?.username}</span>
          <button onClick={saveCurrentTrip} title="Save trip"
            className="p-2 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-white transition-colors">
            <Bookmark size={16}/>
          </button>
          <button onClick={() => setShowTrips(!showTrips)} title="Saved trips"
            className={`p-2 rounded-lg transition-colors ${showTrips ? 'bg-slate-700 text-white' : 'hover:bg-slate-700 text-slate-400 hover:text-white'}`}>
            <History size={16}/>
          </button>
          <button onClick={handleLogout} title="Logout"
            className="p-2 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-red-400 transition-colors">
            <LogOut size={16}/>
          </button>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* Chat */}
        <div className="flex flex-col flex-1 min-w-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map(msg => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] ${msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5' 
                  : 'bg-slate-800 text-slate-100 rounded-2xl rounded-tl-sm px-4 py-3 border border-slate-700'}`}>
                  {msg.loading ? (
                    <div className="flex items-center gap-1 py-1">
                      {[0,1,2].map(i => (
                        <div key={i} className="typing-dot w-2 h-2 bg-blue-400 rounded-full"
                          style={{animationDelay: `${i * 0.2}s`}}/>
                      ))}
                    </div>
                  ) : (
                    <>
                      {msg.role === 'assistant' && msg.intent && (
                        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border mb-2 ${INTENT_COLORS[msg.intent] || INTENT_COLORS.general}`}>
                          {INTENT_ICONS[msg.intent]}
                          {msg.intent}
                        </span>
                      )}
                      <div className={msg.role === 'assistant' ? 'markdown' : ''}>
                        {msg.role === 'assistant' 
                          ? <ReactMarkdown>{msg.content}</ReactMarkdown>
                          : <p className="text-sm">{msg.content}</p>
                        }
                      </div>
                    </>
                  )}
                </div>
              </div>
            ))}
            
            {/* Suggestions (only at start) */}
            {messages.length === 1 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-4">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} onClick={() => send(s.text)}
                    className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 rounded-xl px-3 py-2.5 text-xs text-slate-300 hover:text-white transition-all text-left">
                    <span className="text-blue-400 shrink-0">{s.icon}</span>
                    <span>{s.text}</span>
                  </button>
                ))}
              </div>
            )}
            <div ref={bottomRef}/>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-slate-700 bg-slate-800/50 shrink-0">
            <div className="flex gap-2 items-end">
              <div className="flex-1 bg-slate-800 border border-slate-600 rounded-2xl flex items-end">
                <textarea
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }}}
                  placeholder="Ask about flights, weather, itineraries, currencies..."
                  rows={1}
                  className="flex-1 bg-transparent text-white placeholder-slate-500 px-4 py-3 text-sm resize-none focus:outline-none max-h-32"
                  style={{minHeight: '44px'}}
                />
                <button onClick={listening ? stopVoice : startVoice}
                  className={`p-3 mr-1 rounded-xl transition-colors ${listening ? 'text-red-400 animate-pulse' : 'text-slate-400 hover:text-white'}`}
                  title="Voice input">
                  {listening ? <MicOff size={16}/> : <Mic size={16}/>}
                </button>
              </div>
              <button onClick={() => send()}
                disabled={!input.trim() || loading}
                className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-2xl p-3 transition-colors shrink-0">
                <Send size={16}/>
              </button>
            </div>
          </div>
        </div>

        {/* Right sidebar: Map + Trips */}
        <div className="hidden lg:flex flex-col w-80 border-l border-slate-700 bg-slate-800">
          {/* Map */}
          <div className="flex-1 min-h-0">
            {mapData ? (
              <MapView lat={mapData.lat} lon={mapData.lon} name={mapData.name}/>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-2">
                <Map size={32} className="opacity-30"/>
                <p className="text-sm">Map updates when you ask about a destination</p>
              </div>
            )}
          </div>

          {/* Saved Trips Panel */}
          {showTrips && (
            <div className="border-t border-slate-700 p-4 max-h-64 overflow-y-auto">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <History size={14}/> Saved Trips ({trips.length})
              </h3>
              {trips.length === 0 ? (
                <p className="text-xs text-slate-500">No saved trips yet. Ask for an itinerary and save it!</p>
              ) : (
                <div className="space-y-2">
                  {trips.map((trip: Record<string, unknown>) => (
                    // <div key={trip.id as string} className="bg-slate-700 rounded-xl p-3">
                    <div
  key={trip.id as string}
  className="bg-slate-700 rounded-xl p-3 cursor-pointer hover:bg-slate-600"
  onClick={() => {
      console.log("TRIP:", trip)

    setMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        role: 'assistant',
        content:
          ((trip.itinerary as { content?: string })?.content) ||
          'No itinerary found'
      }
    ])
  }}
//   onClick={() => {
//   alert(JSON.stringify(trip, null, 2))
// }}
>
                      <p className="text-sm font-medium text-white">{trip.title as string}</p>
<p className="text-xs text-slate-400">{trip.destination as string}</p>
{trip.start_date && <p className="text-xs text-slate-500">{trip.start_date as string}</p>}

<button
  className="mt-2 text-red-400 text-xs hover:text-red-300"
  onClick={async (e) => {
    e.stopPropagation()

    if (!confirm("Delete this trip?")) return

    await apiFetch(`/chat/trips/${trip.id}`, {
      method: "DELETE",
    })

    loadTrips()
  }}
>
  Delete Trip
</button>

</div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
