"""Persistent panel supervising a separate, restartable kernel process."""
import argparse
import multiprocessing
import threading
import tkinter as tk
from tkinter import ttk

from .supervisor import Supervisor
from .tokens import persistent_token


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--acceptance',action='store_true')
    parser.add_argument('--reuse-local-token',action='store_true')
    parser.add_argument('--rotate-local-token',action='store_true')
    parser.add_argument('--acceptance-case',choices=('kernel-v1','search-v1.3'),default='kernel-v1')
    args = parser.parse_args()
    window = tk.Tk()
    window.title('Ego 共享内核')
    window.geometry('760x520')
    panel = ttk.Frame(window,padding=18)
    panel.pack(fill='both',expand=True)
    ttk.Label(panel,text='AIRI 与 Minecraft 共用同一内核',font=('Microsoft YaHei UI',15)).pack(anchor='w')
    status = tk.StringVar(value='正在启动内核……')
    ttk.Label(panel,textvariable=status,wraplength=720).pack(anchor='w',pady=12)
    ttk.Label(panel,text='AIRI 地址：http://127.0.0.1:18787/v1/    模型：ego-companion').pack(anchor='w')
    ttk.Label(panel,text='DeepSeek：每日额度 $4，按温尼伯本地零点重置。').pack(anchor='w',pady=8)
    from .d17_panel import add_panel
    add_panel(panel)
    supplied = window.clipboard_get() if args.reuse_local_token else None
    token = persistent_token(supplied=supplied,rotate=args.rotate_local_token)
    token_value = tk.StringVar(value=token)
    token_row = ttk.Frame(panel)
    token_row.pack(fill='x')
    ttk.Label(token_row,text='本机令牌（重启后沿用）：').pack(side='left')
    ttk.Entry(token_row,textvariable=token_value,show='•',width=35,state='readonly').pack(side='left')
    def copy():
        window.clipboard_clear()
        window.clipboard_append(token)
    ttk.Button(token_row,text='复制本机令牌',command=copy).pack(side='left',padx=8)
    supervisor = Supervisor({'acceptance':args.acceptance,'acceptance_case':args.acceptance_case})
    supervisor.start()
    controls = ttk.Frame(panel)
    controls.pack(anchor='w',pady=15)
    for label,command in [('停止当前动作','stop'),('连接 MC','reconnect'),('同步 MC 回复','replay')]:
        ttk.Button(controls,text=label,command=lambda c=command:supervisor.send(c)).pack(side='left',padx=6)
    closing = threading.Event()
    finished = threading.Event()
    def close():
        if closing.is_set(): return
        closing.set()
        status.set('正在停止并保存……')
        def finish():
            supervisor.close()
            finished.set()
        threading.Thread(target=finish,daemon=True).start()
    ttk.Button(controls,text='结束运行',command=close).pack(side='left',padx=6)
    window.protocol('WM_DELETE_WINDOW',close)
    def tick():
        if finished.is_set():
            window.destroy()
            return
        if not closing.is_set(): status.set(supervisor.tick())
        window.after(500,tick)
    tick()
    window.mainloop()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
