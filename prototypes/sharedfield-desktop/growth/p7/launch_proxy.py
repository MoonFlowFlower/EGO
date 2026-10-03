"""Local interactive launch: secrets never enter args, files, or terminal output.

Run from growth: .venv/Scripts/python.exe -m p7.launch_proxy --port 8787
This opens a local Tk credential panel. Starting does only a ZDR preflight;
authenticated chat clients cause metered calls within the shared $5 ledger.
"""
from __future__ import annotations

import argparse
import queue
import threading

from .proxy import DEFAULT_ORIGINS, MODEL, FixedRouteTransport, ProxyError, ProxyServer


def main():
    import tkinter as tk
    from tkinter import ttk

    parser = argparse.ArgumentParser(description="P7 loopback proxy; enter credentials in its local window")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--origin", action="append", default=[], help="Explicit AIRI local webview origin; no credentials")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    panel = tk.Tk()
    panel.title("P7 local proxy")
    panel.geometry("750x330")
    panel.resizable(False, False)
    frame = ttk.Frame(panel, padding=16)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="OpenRouter key (memory only)").grid(row=0, column=0, sticky="w")
    credential = tk.StringVar()
    key_entry = ttk.Entry(frame, textvariable=credential, show="*", width=68)
    key_entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 12))
    ttk.Label(frame, text="Model: " + MODEL).grid(row=2, column=0, columnspan=3, sticky="w")
    ttk.Label(frame, text="Phase 1 shared budget: $5 maximum; fixed ZDR route; no fallbacks").grid(row=3, column=0, columnspan=3, sticky="w")
    status = tk.StringVar(value="Stopped. Keys and tokens are not saved by this panel.")
    ttk.Label(frame, textvariable=status).grid(row=4, column=0, columnspan=3, sticky="w", pady=(10, 6))
    endpoint, token = tk.StringVar(), tk.StringVar()
    ttk.Label(frame, text="Base URL").grid(row=5, column=0, sticky="w")
    ttk.Entry(frame, textvariable=endpoint, state="readonly", width=67).grid(row=6, column=0, columnspan=3, sticky="ew")
    ttk.Label(frame, text="Session token (use only in a client that does not persist it)").grid(row=7, column=0, columnspan=3, sticky="w", pady=(10, 0))
    token_entry = ttk.Entry(frame, textvariable=token, show="*", state="readonly", width=67)
    token_entry.grid(row=8, column=0, columnspan=3, sticky="ew")
    revealed = tk.BooleanVar(value=False)
    ttk.Checkbutton(frame, text="Show session token locally", variable=revealed,
                    command=lambda: token_entry.configure(show="" if revealed.get() else "*")).grid(row=9, column=0, sticky="w", pady=8)
    results, active = queue.Queue(), {"server": None, "generation": 0}

    def create_server(api_key, generation):
        server = None
        try:
            transport = FixedRouteTransport(api_key=api_key)
            transport.preflight()
            server = ProxyServer(transport, port=args.port, allowed_origins=set(DEFAULT_ORIGINS) | set(args.origin))
            server.start()
            results.put((generation, server, None))
        except Exception as error:
            if server:
                server.close()
            results.put((generation, None, error.code if isinstance(error, ProxyError) else "startup_failed"))

    def start():
        api_key = credential.get().strip()
        if not api_key:
            status.set("Enter a key in this window.")
            return
        credential.set("")
        key_entry.configure(state="disabled")
        start_button.configure(state="disabled")
        status.set("Checking fixed ZDR endpoint; no completion request is sent.")
        active["generation"] += 1
        threading.Thread(target=create_server, args=(api_key, active["generation"]), daemon=True).start()

    def stop():
        active["generation"] += 1
        if active["server"] is not None:
            active["server"].close()
            active["server"] = None
        endpoint.set("")
        token.set("")
        revealed.set(False)
        token_entry.configure(show="*")
        key_entry.configure(state="normal")
        start_button.configure(state="normal")
        status.set("Stopped. The previous session token is no longer accepted.")

    def poll():
        try:
            generation, server, error = results.get_nowait()
            if generation != active["generation"]:
                if server:
                    server.close()
            elif error:
                status.set("Startup refused: " + error)
                key_entry.configure(state="normal")
                start_button.configure(state="normal")
            else:
                active["server"] = server
                endpoint.set(server.base_url)
                token.set(server.token)
                status.set("Running on loopback. Chat requests are metered; close to stop.")
        except queue.Empty:
            pass
        panel.after(100, poll)

    def close():
        stop()
        credential.set("")
        panel.destroy()

    start_button = ttk.Button(frame, text="Start", command=start)
    start_button.grid(row=9, column=1, padx=8)
    ttk.Button(frame, text="Stop", command=stop).grid(row=9, column=2)
    panel.protocol("WM_DELETE_WINDOW", close)
    panel.after(100, poll)
    key_entry.focus_set()
    panel.mainloop()


if __name__ == "__main__":
    main()
