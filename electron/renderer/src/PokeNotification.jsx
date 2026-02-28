import { useEffect, useRef, useState } from 'react'

const AUTO_DISMISS_MS = 15000

export default function PokeNotification({ poke, senderName, nudgeResult, userId, onDismiss }) {
    const [feedbackSent, setFeedbackSent] = useState(false)
    const [feedbackValue, setFeedbackValue] = useState(null)
    const timerRef = useRef(null)
    const audioRef = useRef(null)

    // Auto-dismiss timer
    useEffect(() => {
        timerRef.current = setTimeout(onDismiss, AUTO_DISMISS_MS)
        return () => clearTimeout(timerRef.current)
    }, [onDismiss])

    // Play audio
    useEffect(() => {
        if (!nudgeResult?.audio_base64) return
        try {
            const binary = atob(nudgeResult.audio_base64)
            const bytes = new Uint8Array(binary.length)
            for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
            const blob = new Blob([bytes], { type: 'audio/mpeg' })
            const url = URL.createObjectURL(blob)
            audioRef.current = new Audio(url)
            audioRef.current.play().catch(() => { }) // Swallow autoplay error
        } catch { }
    }, [nudgeResult])

    async function sendFeedback(value) {
        setFeedbackValue(value)
        setFeedbackSent(true)
        if (window.electronAPI) {
            await window.electronAPI.feedback({
                poke_id: poke.id,
                user_id: userId,
                user_feedback: value,
            })
        }
        setTimeout(onDismiss, 1200)
    }

    const status = nudgeResult?.status
    const message = nudgeResult?.message_text || `${senderName} sent you a poke! 👋`
    const reasoning = nudgeResult?.classification_reasoning

    return (
        <div className="poke-toast">
            <div className="poke-card">
                {/* Header */}
                <div className="poke-sender">
                    🔔 <strong>{senderName}</strong> sent you a poke!
                    {status && (
                        <span
                            className={`badge ${status === 'OFF_TASK' ? 'badge-off' : 'badge-on'}`}
                            style={{ marginLeft: 8 }}
                            title={reasoning}
                        >
                            {status === 'OFF_TASK' ? 'Off-task' : 'On-task'}
                        </span>
                    )}
                </div>

                {/* Message */}
                <div className="poke-message">{message}</div>

                {/* Feedback */}
                {!feedbackSent ? (
                    <>
                        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>
                            Was this assessment accurate?
                        </p>
                        <div className="feedback-row">
                            <button className="btn btn-ghost" onClick={() => sendFeedback('CORRECT')}>
                                👍 Yes
                            </button>
                            {status === 'OFF_TASK' ? (
                                <button className="btn btn-ghost" onClick={() => sendFeedback('WRONG_OFF_TASK')}>
                                    👎 I was on-task
                                </button>
                            ) : (
                                <button className="btn btn-ghost" onClick={() => sendFeedback('WRONG_ON_TASK')}>
                                    👎 I was off-task
                                </button>
                            )}
                            <button className="btn btn-ghost" style={{ flex: '0 0 auto', padding: '8px 10px' }} onClick={onDismiss}>
                                ✕
                            </button>
                        </div>
                    </>
                ) : (
                    <p style={{ fontSize: 13, color: 'var(--green)', textAlign: 'center', padding: '8px 0' }}>
                        Thanks for the feedback! ✓
                    </p>
                )}
            </div>
        </div>
    )
}
