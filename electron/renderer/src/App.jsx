import { useState, useEffect, useCallback } from 'react'
import { supabase, subscribeToPokes, upsertPresence, subscribeToPresence, getFriends } from './supabase'
import FriendList from './FriendList'
import PokeNotification from './PokeNotification'
import Settings from './Settings'
import Login from './Login'

// Nav icons (inline SVG)
const Icons = {
    friends: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></svg>,
    settings: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3" /><path d="M19.07 4.93a10 10 0 0 0-14.14 0M4.93 19.07a10 10 0 0 0 14.14 0M21.17 8a10 10 0 0 0-1.05-2.37M2.83 8A10 10 0 0 1 3.88 5.63M8 2.83a10 10 0 0 1 2.37-1.05M8 21.17A10 10 0 0 0 10.37 22.22M16 21.17a10 10 0 0 0 2.37-1.05M16 2.83a10 10 0 0 1 2.37 1.05" /></svg>,
}

export default function App() {
    const [session, setSession] = useState(null)
    const [loading, setLoading] = useState(true)
    const [tab, setTab] = useState('friends')
    const [incomingPoke, setIncomingPoke] = useState(null)  // { poke, nudgeResult }
    const [sidecarOk, setSidecarOk] = useState(true)
    const [friends, setFriends] = useState([])
    const [presence, setPresence] = useState({})    // { userId: bool }

    // ── Auth ──────────────────────────────────────────────────────────────────
    useEffect(() => {
        supabase.auth.getSession().then(({ data }) => {
            setSession(data.session)
            setLoading(false)
        })
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_, s) => setSession(s))
        return () => subscription.unsubscribe()
    }, [])

    // ── Sidecar monitoring ────────────────────────────────────────────────────
    useEffect(() => {
        const id = setInterval(async () => {
            if (window.electronAPI) {
                const ok = await window.electronAPI.health()
                setSidecarOk(ok)
            }
        }, 10000)
        return () => clearInterval(id)
    }, [])

    // ── Load friends + presence ───────────────────────────────────────────────
    useEffect(() => {
        if (!session?.user) return
        const userId = session.user.id

        // Upsert presence as online
        upsertPresence(userId, true)

        // Heartbeat every 30s
        const heartbeat = setInterval(() => upsertPresence(userId, true), 30000)

        // Mark offline on unload
        window.addEventListener('beforeunload', () => upsertPresence(userId, false))

        // Fetch friends
        getFriends(userId).then((list) => {
            setFriends(list)
            // Fetch their presence
            supabase
                .from('presence')
                .select('user_id, is_online')
                .in('user_id', list.map((f) => f.id))
                .then(({ data }) => {
                    if (data) {
                        const map = {}
                        data.forEach((p) => { map[p.user_id] = p.is_online })
                        setPresence(map)
                    }
                })
            // Subscribe to presence changes
            subscribeToPresence(
                list.map((f) => f.id),
                (updated) => setPresence((p) => ({ ...p, [updated.user_id]: updated.is_online }))
            )
        })

        return () => clearInterval(heartbeat)
    }, [session])

    // ── Subscribe to incoming pokes ───────────────────────────────────────────
    useEffect(() => {
        if (!session?.user) return
        const channel = subscribeToPokes(session.user.id, async (poke) => {
            // Fetch sender name
            const { data: sender } = await supabase
                .from('users')
                .select('display_name')
                .eq('id', poke.sender_id)
                .single()
            const senderName = sender?.display_name || 'A friend'

            // Call sidecar nudge
            let nudgeResult = null
            if (window.electronAPI) {
                try { nudgeResult = await window.electronAPI.nudge(senderName) } catch { }
            }
            setIncomingPoke({ poke, senderName, nudgeResult })
        })
        return () => { supabase.removeChannel(channel) }
    }, [session])

    if (loading) return null

    if (!session) return <Login onLogin={setSession} />

    return (
        <div className="app-layout">
            {/* Header */}
            <header className="header">
                <span className="logo">mistral<span>hack</span></span>
                <div className="header-actions">
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        {session.user.email?.split('@')[0]}
                    </span>
                </div>
            </header>

            {/* Sidecar warning */}
            {!sidecarOk && (
                <div className="sidecar-banner">
                    ⚠ AI service unavailable — nudges disabled
                </div>
            )}

            {/* Main content */}
            <div className="scroll-area">
                {tab === 'friends' && (
                    <FriendList
                        friends={friends}
                        presence={presence}
                        currentUserId={session.user.id}
                    />
                )}
                {tab === 'settings' && (
                    <Settings userId={session.user.id} />
                )}
            </div>

            {/* Bottom nav */}
            <nav className="nav">
                <button className={`nav-btn ${tab === 'friends' ? 'active' : ''}`} onClick={() => setTab('friends')}>
                    {Icons.friends}Friends
                </button>
                <button className={`nav-btn ${tab === 'settings' ? 'active' : ''}`} onClick={() => setTab('settings')}>
                    {Icons.settings}Settings
                </button>
            </nav>

            {/* Incoming poke overlay */}
            {incomingPoke && (
                <PokeNotification
                    poke={incomingPoke.poke}
                    senderName={incomingPoke.senderName}
                    nudgeResult={incomingPoke.nudgeResult}
                    userId={session.user.id}
                    onDismiss={() => setIncomingPoke(null)}
                />
            )}
        </div>
    )
}
