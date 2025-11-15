import { contextBridge } from 'electron'

// Expose limited API to renderer
contextBridge.exposeInMainWorld('electronAPI', {
  version: process.versions.electron,
  platform: process.platform,
})
