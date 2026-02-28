import { useState, useEffect } from 'react'

const STORAGE_KEY = 'mistralhack-settings'

const defaults = {
    voiceEnabled: true,
    volume: 75,
    muteStart: '22:00',
    muteEnd: '08:00',
    privacyMode: false,
    useLocalModel: false,
}

export default function Settings({ userId }) {
    const [cfg, setCfg] = useState(() => {
        try { return { ...defaults, ...JSON.parse(localStorage.getItem(STORAGE_KEY)) } }
        catch { return defaults }
    })

    // Persist and push to sidecar on every change
    useEffect(() => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg))
        if (window.electronAPI) {
            window.electronAPI.updateConfig({
                privacy_mode: cfg.privacyMode,
                use_local_model: cfg.useLocalModel,
                mute_start: cfg.muteStart,
                mute_end: cfg.muteEnd,
            }).catch(() => { })
        }
    }, [cfg])

    function set(key, value) {
        setCfg((prev) => ({ ...prev, [key]: value }))
    }

    return (
        <div>
            {/* Voice */}
            <div className="settings-section">
                <div className="settings-label">Voice & Audio</div>

                <ToggleRow
                    label="Enable voice nudges"
                    sub="Plays audio when you receive a poke"
                    checked={cfg.voiceEnabled}
                    onChange={(v) => set('voiceEnabled', v)}
                />

                <div className="toggle-row">
                    <div>
                        <div className="toggle-row-label">Volume</div>
                        <div className="toggle-row-sub">{cfg.volume}%</div>
                    </div>
                    <input
                        type="range" min="0" max="100"
                        value={cfg.volume}
                        onChange={(e) => set('volume', Number(e.target.value))}
                        style={{ width: 120 }}
                    />
                </div>

                <div className="toggle-row">
                    <div>
                        <div className="toggle-row-label">Mute hours</div>
                        <div className="toggle-row-sub">No audio during these hours</div>
                    </div>
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                        <input
                            type="time" value={cfg.muteStart}
                            onChange={(e) => set('muteStart', e.target.value)}
                            className="input" style={{ width: 90, padding: '6px 8px' }}
                        />
                        <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>to</span>
                        <input
                            type="time" value={cfg.muteEnd}
                            onChange={(e) => set('muteEnd', e.target.value)}
                            className="input" style={{ width: 90, padding: '6px 8px' }}
                        />
                    </div>
                </div>
            </div>

            {/* Privacy */}
            <div className="settings-section">
                <div className="settings-label">Privacy & AI</div>

                <ToggleRow
                    label="Privacy mode"
                    sub="Anonymises window titles before classification"
                    checked={cfg.privacyMode}
                    onChange={(v) => set('privacyMode', v)}
                />

                <ToggleRow
                    label="Use local AI (offline)"
                    sub="Routes to Ollama instead of cloud API"
                    checked={cfg.useLocalModel}
                    onChange={(v) => set('useLocalModel', v)}
                />
            </div>

            {/* Account */}
            <div className="settings-section">
                <div className="settings-label">Account</div>
                <div className="toggle-row">
                    <div className="toggle-row-label">User ID</div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                        {userId?.slice(0, 8)}…
                    </div>
                </div>
                <button
                    className="btn btn-danger"
                    style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}
                    onClick={() => {
                        const { supabase } = require('./supabase')
                        supabase.auth.signOut()
                    }}
                >
                    Sign out
                </button>
            </div>
        </div>
    )
}

function ToggleRow({ label, sub, checked, onChange }) {
    return (
        <div className="toggle-row">
            <div>
                <div className="toggle-row-label">{label}</div>
                {sub && <div className="toggle-row-sub">{sub}</div>}
            </div>
            <label className="switch">
                <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
                <span className="slider" />
            </label>
        </div>
    )
}
