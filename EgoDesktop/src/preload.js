const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("egoDesktop", {
  getConfig: () => ipcRenderer.invoke("ego-desktop:get-config"),
  sendChatTurn: (payload) => ipcRenderer.invoke("ego-desktop:chat-turn", payload),
  synthesizeSpeech: (payload) => ipcRenderer.invoke("ego-desktop:synthesize-speech", payload),
  cancelSpeech: () => ipcRenderer.invoke("ego-desktop:cancel-speech"),
  reportReady: (payload) => ipcRenderer.send("ego-desktop:renderer-ready", payload),
});
