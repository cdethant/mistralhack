/**
 * Electron main process
 * - Spawns Python sidecar on startup
 * - Polls /health until ready (30s timeout)
 * - Loads the React renderer
 * - Gracefully cleans up sidecar on quit
 */
const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const http = require('http')

const SIDECAR_PORT = 8765
const DEV_MODE = process.env.NODE_ENV === 'development'

let mainWindow = null
let sidecarProcess = null

// ── Sidecar lifecycle ──────────────────────────────────────────────────────────
function spawnSidecar() {
    const sidecarPath = path.join(__dirname, '..', '..', 'sidecar', 'main.py')
    const venvPython = path.join(__dirname, '..', '..', 'sidecar', 'venv', 'bin', 'python')
    const python = require('fs').existsSync(venvPython) ? venvPython : 'python3'

    sidecarProcess = spawn(python, [sidecarPath], {
        cwd: path.join(__dirname, '..', '..', 'sidecar'),
        env: { ...process.env },
        stdio: ['ignore', 'pipe', 'pipe'],
    })

    sidecarProcess.stdout.on('data', (d) => console.log('[sidecar]', d.toString().trim()))
    sidecarProcess.stderr.on('data', (d) => console.error('[sidecar-err]', d.toString().trim()))
    sidecarProcess.on('exit', (code) => console.log(`[sidecar] exited with code ${code}`))
}

function checkHealth() {
    return new Promise((resolve) => {
        http
            .get(`http://localhost:${SIDECAR_PORT}/health`, (res) => {
                resolve(res.statusCode === 200)
            })
            .on('error', () => resolve(false))
    })
}

async function waitForSidecar(timeoutMs = 30000) {
    const start = Date.now()
    while (Date.now() - start < timeoutMs) {
        const ok = await checkHealth()
        if (ok) return true
        await new Promise((r) => setTimeout(r, 500))
    }
    return false
}

// ── Window ─────────────────────────────────────────────────────────────────────
async function createWindow() {
    mainWindow = new BrowserWindow({
        width: 420,
        height: 680,
        minWidth: 360,
        minHeight: 500,
        titleBarStyle: 'hiddenInset',
        backgroundColor: '#0a0a0f',
        webPreferences: {
            preload: path.join(__dirname, '..', 'preload', 'index.js'),
            contextIsolation: true,
            nodeIntegration: false,
        },
    })

    if (DEV_MODE) {
        mainWindow.loadURL('http://localhost:5173')
        mainWindow.webContents.openDevTools()
    } else {
        mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'dist', 'index.html'))
    }
}

// ── IPC handlers ───────────────────────────────────────────────────────────────
ipcMain.handle('sidecar:nudge', async (_, senderName) => {
    const res = await fetch(`http://localhost:${SIDECAR_PORT}/nudge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender_name: senderName }),
    })
    return res.json()
})

ipcMain.handle('sidecar:feedback', async (_, payload) => {
    const res = await fetch(`http://localhost:${SIDECAR_PORT}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
    return res.json()
})

ipcMain.handle('sidecar:config', async (_, configPayload) => {
    const res = await fetch(`http://localhost:${SIDECAR_PORT}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configPayload),
    })
    return res.json()
})

ipcMain.handle('sidecar:health', async () => {
    return checkHealth()
})

// ── App lifecycle ──────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
    spawnSidecar()
    await createWindow()

    const ready = await waitForSidecar()
    if (mainWindow) {
        mainWindow.webContents.send('sidecar:ready', ready)
    }
})

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
    if (sidecarProcess) {
        sidecarProcess.kill('SIGTERM')
    }
})

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
