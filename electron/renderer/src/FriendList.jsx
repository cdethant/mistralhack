import { useState } from 'react'
import { supabase, sendPoke, updatePokeClassification } from './supabase'

export default function FriendList({ friends, presence, currentUserId }) {
    const [pokingId, setPokingId] = useState(null) // which friend is being poked
    const [lastPokeStatus, setLastPokeStatus] = useState({}) // { friendId: 'sent'|'error' }

    const onlineFriends = friends.filter((f) => presence[f.id])
    const offlineFriends = friends.filter((f) => !presence[f.id])

    async function handlePoke(friend) {
        if (pokingId) return
        setPokingId(friend.id)

        // Insert poke row in Supabase
        const { data: poke, error } = await sendPoke(currentUserId, friend.id)
        if (error) {
            setLastPokeStatus((s) => ({ ...s, [friend.id]: 'error' }))
            setPokingId(null)
            return
        }

        setLastPokeStatus((s) => ({ ...s, [friend.id]: 'sent' }))
        setTimeout(() => setLastPokeStatus((s) => ({ ...s, [friend.id]: null })), 3000)
        setPokingId(null)
    }

    async function handlePokeAll() {
        for (const friend of onlineFriends) {
            await handlePoke(friend)
        }
    }

    if (friends.length === 0) {
        return <p className="empty">No friends yet. Ask a teammate to sign up! 👋</p>
    }

    return (
        <div>
            {/* Online */}
            {onlineFriends.length > 0 && (
                <>
                    <div className="section-header">
                        <span className="section-title">Online ({onlineFriends.length})</span>
                        {onlineFriends.length > 1 && (
                            <button className="btn btn-ghost" style={{ fontSize: 12, padding: '5px 10px' }} onClick={handlePokeAll}>
                                Poke All 👋
                            </button>
                        )}
                    </div>
                    {onlineFriends.map((f) => (
                        <FriendRow
                            key={f.id}
                            friend={f}
                            online
                            poking={pokingId === f.id}
                            status={lastPokeStatus[f.id]}
                            onPoke={() => handlePoke(f)}
                        />
                    ))}
                </>
            )}

            {/* Offline */}
            {offlineFriends.length > 0 && (
                <>
                    <div className="section-header" style={{ marginTop: onlineFriends.length > 0 ? 20 : 0 }}>
                        <span className="section-title">Offline ({offlineFriends.length})</span>
                    </div>
                    {offlineFriends.map((f) => (
                        <FriendRow key={f.id} friend={f} online={false} />
                    ))}
                </>
            )}
        </div>
    )
}

function FriendRow({ friend, online, poking, status, onPoke }) {
    const initials = friend.display_name
        ? friend.display_name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
        : '??'

    return (
        <div className="friend-row">
            <div className="friend-avatar">{initials}</div>
            <div className="friend-info">
                <div className="friend-name">{friend.display_name}</div>
                <div className="friend-status">{online ? 'Online' : 'Offline'}</div>
            </div>
            <div className={`dot ${online ? 'dot-online' : 'dot-offline'}`} />
            {online && (
                <button
                    className={`btn btn-primary btn-poke`}
                    style={{ padding: '6px 14px', fontSize: 13 }}
                    disabled={poking}
                    onClick={onPoke}
                >
                    {poking ? '…' : status === 'sent' ? '✓ Sent' : status === 'error' ? '✗ Err' : '👋 Poke'}
                </button>
            )}
        </div>
    )
}
