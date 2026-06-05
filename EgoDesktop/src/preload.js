const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("egoDesktop", {
  getConfig: () => ipcRenderer.invoke("ego-desktop:get-config"),
  openDeveloperSettings: () => ipcRenderer.invoke("ego-desktop:open-developer-settings"),
  getDeveloperSettings: () => ipcRenderer.invoke("ego-desktop:get-developer-settings"),
  saveDeveloperSettings: (payload) => ipcRenderer.invoke("ego-desktop:save-developer-settings", payload),
  getEffectiveLaunchConfig: () => ipcRenderer.invoke("ego-desktop:get-effective-launch-config"),
  applyLiveDeveloperSettings: (payload) => ipcRenderer.invoke("ego-desktop:apply-live-developer-settings", payload),
  onDeveloperSettingsUpdated: (callback) => {
    const listener = (_event, payload) => callback(payload);
    ipcRenderer.on("ego-desktop:developer-settings-updated", listener);
    return () => ipcRenderer.off("ego-desktop:developer-settings-updated", listener);
  },
  onPspcReplyPreviewUpdated: (callback) => {
    const listener = (_event, payload) => callback(payload);
    ipcRenderer.on("ego-desktop:pspc-reply-preview-updated", listener);
    return () => ipcRenderer.off("ego-desktop:pspc-reply-preview-updated", listener);
  },
  sendChatTurn: (payload) => ipcRenderer.invoke("ego-desktop:chat-turn", payload),
  synthesizeSpeech: (payload) => ipcRenderer.invoke("ego-desktop:synthesize-speech", payload),
  cancelSpeech: () => ipcRenderer.invoke("ego-desktop:cancel-speech"),
  reportReady: (payload) => ipcRenderer.send("ego-desktop:renderer-ready", payload),
});
