import { useState } from 'react'
import { supabase } from './supabase'

export default function Login({ onLogin }) {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(false)
    const [mode, setMode] = useState('login') // 'login' | 'signup'

    async function handleSubmit(e) {
        e.preventDefault()
        setError(null)
        setLoading(true)

        let result
        if (mode === 'login') {
            result = await supabase.auth.signInWithPassword({ email, password })
        } else {
            result = await supabase.auth.signUp({ email, password })
        }

        setLoading(false)
        if (result.error) {
            setError(result.error.message)
        } else {
            onLogin(result.data.session)
        }
    }

    return (
        <div className="login-wrap">
            <div>
                <div className="login-title">mistral<span>hack</span></div>
                <p className="login-sub" style={{ marginTop: 8 }}>Stay accountable with your team 🎯</p>
            </div>

            <form className="login-form" onSubmit={handleSubmit}>
                <input
                    className="input"
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                />
                <input
                    className="input"
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                />

                {error && <p className="login-error">{error}</p>}

                <button className="btn btn-primary" type="submit" disabled={loading} style={{ justifyContent: 'center' }}>
                    {loading ? 'Loading…' : mode === 'login' ? 'Sign in' : 'Create account'}
                </button>

                <button
                    type="button"
                    className="btn btn-ghost"
                    style={{ justifyContent: 'center', fontSize: 12 }}
                    onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError(null) }}
                >
                    {mode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
                </button>
            </form>
        </div>
    )
}
