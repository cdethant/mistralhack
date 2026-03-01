import { app, BrowserWindow, ipcMain, Notification } from 'electron';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import started from 'electron-squirrel-startup';

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (started) {
  app.quit();
}

const SIDECAR_PORT = 8080;
let sidecarProcess = null;

function startSidecar() {
  // Resolve path: ui-electron/src/main.js -> mistralhack/sidecar/
  const sidecarDir = path.join(__dirname, '..', '..', '..', 'sidecar');
  console.log(`[Sidecar] Starting from: ${sidecarDir}`);

  sidecarProcess = spawn('python3', ['main.py'], {
    cwd: sidecarDir,
    env: { ...process.env },
  });

  sidecarProcess.stdout.on('data', (data) => {
    console.log(`[Sidecar] ${data.toString().trim()}`);
  });

  sidecarProcess.stderr.on('data', (data) => {
    console.error(`[Sidecar ERR] ${data.toString().trim()}`);
  });

  sidecarProcess.on('exit', (code) => {
    console.log(`[Sidecar] Exited with code ${code}`);
    sidecarProcess = null;
  });
}

function stopSidecar() {
  if (sidecarProcess) {
    console.log('[Sidecar] Stopping...');
    sidecarProcess.kill();
    sidecarProcess = null;
  }
}

const createWindow = () => {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  // and load the index.html of the app.
  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`));
  }

  // Open the DevTools.
  mainWindow.webContents.openDevTools();
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  // Start the sidecar background process
  startSidecar();

  // Handle IPC for hostname
  ipcMain.handle('get-hostname', () => os.hostname());

  // Handle triggering notifications for received pokes
  ipcMain.on('trigger-poke-notification', (event, data) => {
    const { senderName } = data;
    new Notification({
      title: 'You got poked!',
      body: `${senderName || 'A friend'} poked you. Get back to work!`
    }).show();
  });

  // Proxy HTTP calls to the sidecar so the sandboxed renderer doesn't need fetch access
  ipcMain.handle('call-sidecar', async (event, { path: sidecarPath, method = 'GET' }) => {
    const url = `http://127.0.0.1:${SIDECAR_PORT}${sidecarPath}`;
    try {
      const response = await fetch(url, { method });
      const data = await response.json();
      console.log(`[Sidecar IPC] ${method} ${sidecarPath} →`, data);
      return { ok: true, data };
    } catch (err) {
      console.error(`[Sidecar IPC] Failed to reach sidecar: ${err.message}`);
      return { ok: false, error: err.message };
    }
  });

  createWindow();

  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  stopSidecar();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', stopSidecar);

