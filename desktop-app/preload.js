const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    startServer: () => ipcRenderer.invoke('start-server'),
    stopServer: () => ipcRenderer.invoke('stop-server'),
    getLocalIP: () => ipcRenderer.invoke('get-local-ip'),
    isServerRunning: () => ipcRenderer.invoke('is-server-running'),
    
    // Event listeners
    onServerLog: (callback) => {
        ipcRenderer.on('server-log', (event, data) => callback(data));
    },
    onServerStopped: (callback) => {
        ipcRenderer.on('server-stopped', callback);
    },
    
    // Remove listeners
    removeAllListeners: (channel) => {
        ipcRenderer.removeAllListeners(channel);
    }
});
