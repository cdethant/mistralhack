import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co'
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder'

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// ── Helper: subscribe to incoming pokes ───────────────────────────────────────
export function subscribeToPokes(userId, onPoke) {
    return supabase
        .channel(`pokes:${userId}`)
        .on(
            'postgres_changes',
            {
                event: 'INSERT',
                schema: 'public',
                table: 'pokes',
                filter: `receiver_id=eq.${userId}`,
            },
            (payload) => onPoke(payload.new)
        )
        .subscribe()
}

// ── Helper: update presence ───────────────────────────────────────────────────
export async function upsertPresence(userId, isOnline) {
    return supabase.from('presence').upsert(
        { user_id: userId, is_online: isOnline, last_seen_at: new Date().toISOString() },
        { onConflict: 'user_id' }
    )
}

// ── Helper: subscribe to friend presence ─────────────────────────────────────
export function subscribeToPresence(friendIds, onChange) {
    return supabase
        .channel('presence-updates')
        .on(
            'postgres_changes',
            { event: '*', schema: 'public', table: 'presence' },
            (payload) => {
                if (friendIds.includes(payload.new?.user_id)) onChange(payload.new)
            }
        )
        .subscribe()
}

// ── Helper: send a poke ───────────────────────────────────────────────────────
export async function sendPoke(senderId, receiverId) {
    const { data, error } = await supabase
        .from('pokes')
        .insert({ sender_id: senderId, receiver_id: receiverId })
        .select()
        .single()
    return { data, error }
}

// ── Helper: update poke with classification result ────────────────────────────
export async function updatePokeClassification(pokeId, status, confidence, reasoning) {
    return supabase.from('pokes').update({
        classification: status,
        confidence,
        classification_reasoning: reasoning,
    }).eq('id', pokeId)
}

// ── Helper: get friends ───────────────────────────────────────────────────────
export async function getFriends(userId) {
    const { data, error } = await supabase
        .from('friendships')
        .select(`
      id,
      user_a:users!user_a_id(id, display_name, avatar_url),
      user_b:users!user_b_id(id, display_name, avatar_url)
    `)
        .or(`user_a_id.eq.${userId},user_b_id.eq.${userId}`)

    if (error) return []

    // Normalize: always return the OTHER user
    return data.map((f) =>
        f.user_a.id === userId ? f.user_b : f.user_a
    )
}
