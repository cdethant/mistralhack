import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
    getHostname: () => ipcRenderer.invoke('get-hostname'),
    triggerPokeNotification: (senderName) => ipcRenderer.send('trigger-poke-notification', { senderName }),
    callSidecar: (path, method = 'GET') => ipcRenderer.invoke('call-sidecar', { path, method }),
});
