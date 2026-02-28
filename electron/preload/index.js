/**
 * Preload script – exposes a typed API surface to the renderer via contextBridge.
 * No raw ipcRenderer / Node.js access in the renderer process.
 */
const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
    // Nudge (poke received)
    nudge: (senderName) => ipcRenderer.invoke('sidecar:nudge', senderName),
    // Feedback submission
    feedback: (payload) => ipcRenderer.invoke('sidecar:feedback', payload),
    // Config update
    updateConfig: (cfg) => ipcRenderer.invoke('sidecar:config', cfg),
    // Health check
    health: () => ipcRenderer.invoke('sidecar:health'),
    // Listen for sidecar ready event
    onSidecarReady: (cb) => ipcRenderer.on('sidecar:ready', (_, ok) => cb(ok)),
})
