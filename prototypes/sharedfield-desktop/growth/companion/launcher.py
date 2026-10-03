"""Local owner panel; started independently of any Codex tool process."""
import argparse
import queue
import threading
import tkinter as tk
from tkinter import ttk

from .runtime import Runtime


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--acceptance',action='store_true')
    parser.add_argument('--acceptance-case',choices=('kernel-v1','search-v1.3'),default='kernel-v1')
    args=parser.parse_args()
    window=tk.Tk()
    window.title('Ego 共享内核'+(' · 工程验收' if args.acceptance else ''))
    window.geometry('720x300')
    window.resizable(False,False)
    panel=ttk.Frame(window,padding=18);panel.pack(fill='both',expand=True)
    ttk.Label(panel,text='AIRI 与 Minecraft 共用同一内核',font=('Microsoft YaHei UI',15)).pack(anchor='w')
    status=tk.StringVar(value='正在检查模型路线、预算和本机连接……')
    ttk.Label(panel,textvariable=status,wraplength=680).pack(anchor='w',pady=12)
    ttk.Label(panel,text='AIRI 地址：http://127.0.0.1:18787/v1/    模型：ego-companion').pack(anchor='w')
    ttk.Label(panel,text='本次运行最多 30 分钟；关闭此窗口会结束身体和内核。').pack(anchor='w',pady=8)
    token=tk.StringVar()
    token_row=ttk.Frame(panel);token_row.pack(fill='x')
    ttk.Label(token_row,text='本机连接令牌：').pack(side='left')
    ttk.Entry(token_row,textvariable=token,show='•',width=42,state='readonly').pack(side='left')
    holder={}
    messages=queue.Queue()
    def copy():
        if token.get():window.clipboard_clear();window.clipboard_append(token.get())
    ttk.Button(token_row,text='复制本机令牌',command=copy).pack(side='left',padx=8)
    controls=ttk.Frame(panel);controls.pack(anchor='w',pady=15)
    def stop():
        if holder.get('runtime'):threading.Thread(target=holder['runtime'].engine.stop,daemon=True).start()
    def reconnect():
        if holder.get('runtime'):threading.Thread(target=holder['runtime'].reconnect_body,daemon=True).start()
    ttk.Button(controls,text='停止当前动作',command=stop).pack(side='left')
    ttk.Button(controls,text='连接 MC',command=reconnect).pack(side='left',padx=10)
    def close():
        status.set('正在停止并保存……')
        def finish():
            if holder.get('runtime'):holder['runtime'].close('owner_closed')
            messages.put(('closed',None))
        threading.Thread(target=finish,daemon=True).start()
    ttk.Button(controls,text='结束本次运行',command=close).pack(side='left')
    def replay():
        if holder.get('runtime'):threading.Thread(target=holder['runtime'].replay_latest_mc,daemon=True).start()
    ttk.Button(controls,text='同步 MC 回复',command=replay).pack(side='left',padx=10)
    window.protocol('WM_DELETE_WINDOW',close)
    def boot():
        try:messages.put(('ready',Runtime(acceptance=args.acceptance,acceptance_case=args.acceptance_case)))
        except Exception as error:messages.put(('error',type(error).__name__))
    def tick():
        try:
            while True:
                kind,value=messages.get_nowait()
                if kind=='ready':holder['runtime']=value;token.set(value.server.token)
                elif kind=='error':status.set('启动失败：'+value+'；详情见本机生命周期记录。')
                elif kind=='closed':window.destroy();return
        except queue.Empty:pass
        if holder.get('runtime'):status.set(holder['runtime'].status())
        window.after(500,tick)
    threading.Thread(target=boot,daemon=True).start()
    tick();window.mainloop()


if __name__=='__main__':main()
