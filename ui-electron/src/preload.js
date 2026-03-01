import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
    getHostname: () => ipcRenderer.invoke('get-hostname'),
    triggerPokeNotification: (senderName) => ipcRenderer.send('trigger-poke-notification', { senderName }),
    callSidecar: (path, method = 'GET', body = null) => ipcRenderer.invoke('call-sidecar', { path, method, body }),
    showRoastOverlay: (data) => ipcRenderer.send('show-roast-overlay', data),
    closeRoastOverlay: () => ipcRenderer.send('close-roast-overlay'),
    onPlayRoast: (callback) => ipcRenderer.on('play-roast', (_event, data) => callback(data)),

});
