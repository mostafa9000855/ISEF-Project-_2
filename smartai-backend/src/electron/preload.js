const { contextBridge, ipcRenderer } = require('electron');

// Expose safe IPC methods to renderer process
contextBridge.exposeInMainWorld('smartaiAPI', {
  // System stats
  getSystemStats: () => ipcRenderer.invoke('get-system-stats'),
  getRiskScore: () => ipcRenderer.invoke('get-risk-score'),
  getCoreHealth: () => ipcRenderer.invoke('get-core-health'),
  getPythonHealth: () => ipcRenderer.invoke('get-python-health'),

  // Actions
  activateVPN: () => ipcRenderer.invoke('activate-vpn'),
  exportReport: (data) => ipcRenderer.invoke('export-report', data),
  openURL: (url) => ipcRenderer.invoke('open-external-url', url),

  // Event listeners
  onSystemStats: (callback) => ipcRenderer.on('system-stats', (event, data) => callback(data)),
  onThreatAlert: (callback) => ipcRenderer.on('threat-alert', (event, data) => callback(data)),

  // Version info
  getVersion: () => '1.0.0'
});
