import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
    getHostname: () => ipcRenderer.invoke('get-hostname'),
});
