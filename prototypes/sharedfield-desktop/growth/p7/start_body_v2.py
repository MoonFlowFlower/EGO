"""Owner launcher: use the LOCAL token from the running P7 proxy panel."""
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading

from growthlab.records import ROOT


def main():
    import tkinter as tk
    from tkinter import ttk
    panel=tk.Tk()
    panel.title('P7 Mindcraft body')
    panel.geometry('680x300')
    frame=ttk.Frame(panel,padding=16);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Open your Java 1.21.1 server or LAN world. Player: Moonlight.').pack(anchor='w')
    ttk.Label(frame,text='Only 127.0.0.1; generated code, voice and screen capture remain off.').pack(anchor='w')
    ttk.Label(frame,text='Local server/LAN port (current server: 25565)').pack(anchor='w',pady=(10,0))
    port=tk.StringVar(value='25565');ttk.Entry(frame,textvariable=port,width=12).pack(anchor='w')
    ttk.Label(frame,text='Local P7 session token (not your cloud API key)').pack(anchor='w',pady=(10,0))
    token=tk.StringVar();ttk.Entry(frame,textvariable=token,show='*',width=75).pack(anchor='w')
    status=tk.StringVar(value='Stopped. Start the proxy first, then paste its local session token.')
    ttk.Label(frame,textvariable=status,wraplength=640).pack(anchor='w',pady=12)
    messages=queue.Queue()
    active={'process':None}
    root=Path('D:/Project/AIProject/MyProject/Ego_proejct_restart/p7_tools/mindcraft')

    def start():
        if active['process'] and active['process'].poll() is None:return
        local=token.get().strip()
        try:
            number=int(port.get())
            if not 1024<=number<=65535 or len(local)<32 or local.startswith('sk-'):
                raise ValueError()
        except ValueError:
            status.set('Enter a LAN port and the local proxy token. Cloud keys are refused.')
            return
        child=subprocess.Popen([sys.executable,'-m','p7.body_session_v2','--private-pipe'],cwd=ROOT,
                               stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                               text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
        active['process']=child
        child.stdin.write(json.dumps({'root':str(root),'host':'127.0.0.1','port':number,'local_token':local})+'\n')
        child.stdin.flush();token.set('')
        status.set('Starting Mindcraft; official logs stay under growth/runs/p7/body_connected_v2.')
        def watch():
            child_closed=False
            for line in child.stdout:
                try:
                    row=json.loads(line)
                    child_closed=child_closed or row.get('kind')=='supervisor_closed'
                    messages.put(row)
                except ValueError:pass
            parent_code=child.wait()
            if not child_closed:messages.put({'kind':'process_exit','code':parent_code})
            child.stdout.close()
        threading.Thread(target=watch,daemon=True).start()

    def stop():
        child=active['process']
        active['process']=None
        if child is not None:
            try:
                if child.poll() is None:
                    child.stdin.write('{"op":"shutdown"}\n');child.stdin.flush()
                    child.wait(timeout=7)
            except (OSError,subprocess.TimeoutExpired):
                if child.poll() is None:child.kill();child.wait(timeout=5)
            finally:
                if child.stdin:child.stdin.close()
        status.set('Stopped. The proxy and AIRI remain separate.')

    def poll():
        while not messages.empty():
            row=messages.get()
            if row.get('kind')=='state' and row.get('state'):
                state=row['state'];status.set('In world: '+state['name']+' | '+state['action']['current']+' | Chat to her in MC as Moonlight.')
            elif row.get('kind')=='supervisor_closed':
                status.set('Body child stopped: '+str(row.get('child_exit'))+'. See the latest body_connected_v2 log.')
            elif row.get('kind') in ('supervisor_error','process_exit'):
                status.set('Body stopped: '+str(row.get('error_type',row.get('code')))+'. See the latest body_connected_v2 log.')
        panel.after(250,poll)

    buttons=ttk.Frame(frame);buttons.pack(anchor='e')
    ttk.Button(buttons,text='Start Mindcraft',command=start).pack(side='left',padx=6)
    ttk.Button(buttons,text='Stop Mindcraft',command=stop).pack(side='left')
    def close():stop();token.set('');panel.destroy()
    panel.protocol('WM_DELETE_WINDOW',close);panel.after(250,poll);panel.mainloop()


if __name__=='__main__':main()
