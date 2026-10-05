"""Nonblocking account/status controls; never changes the production route."""
import queue
import threading
import tkinter as tk
from tkinter import ttk
import webbrowser

from .chatgpt import UsageLedger
from .chatgpt_oauth import Credentials, ChatGPTError, login, disconnect


def add_panel(parent):
    panel = ttk.LabelFrame(parent, text='ChatGPT 套餐 · D17 合成试跑', padding=8)
    panel.pack(fill='x', pady=8)
    status = tk.StringVar(value='正在读取连接状态……')
    ttk.Label(panel, textvariable=status, wraplength=720).pack(anchor='w')
    account = ttk.Combobox(panel, state='readonly', width=55)
    account.pack(anchor='w', pady=4)
    rows, results = {}, queue.Queue()
    busy = False
    def task(operation):
        nonlocal busy
        if busy:
            return
        busy = True
        selected = rows.get(account.get())
        status.set('等待浏览器授权……' if operation == 'login' else '正在断开并撤销授权……')
        def worker():
            try:
                result = login(account_id=selected) if operation == 'login' else disconnect()
                results.put(('operation', result))
            except ChatGPTError as error:
                results.put(('error', error.code))
            except Exception as error:
                results.put(('error', type(error).__name__))
        threading.Thread(target=worker, daemon=True).start()
    buttons = ttk.Frame(panel); buttons.pack(anchor='w')
    ttk.Button(buttons, text='Continue with ChatGPT', command=lambda: task('login')).pack(side='left')
    ttk.Button(buttons, text='断开 ChatGPT', command=lambda: task('disconnect')).pack(side='left', padx=8)
    ttk.Button(buttons, text='Manage usage', command=lambda: webbrowser.open('https://chatgpt.com/settings/usage')).pack(side='left')
    ttk.Label(panel, text='默认使用 DeepSeek；此连接仅供合成试跑。请关闭 credits 或把本应用周上限设为低于 100%。', wraplength=720).pack(anchor='w')
    ticks = 0
    def poll():
        nonlocal busy, ticks
        while not results.empty():
            kind, result = results.get_nowait()
            if kind == 'status':
                connection, usage = result
                old = account.get()
                rows.clear(); rows['添加另一个 ChatGPT 账户'] = None
                rows.update({f"{a.get('email') or 'ChatGPT'} · {a['id'][-6:]}": a['id'] for a in connection['accounts']})
                account['values'] = list(rows)
                account.set(old if old in rows else next(iter(rows)))
                state = '已连接' if connection['connected'] else '未连接'
                if connection['connected'] and not connection['plan_enabled']:
                    state = '已登录，未授权套餐用量'
                status.set(f"{state} · {connection.get('account') or ''} · {usage['calls']} 次 · "
                           f"输入 {usage['input_tokens']} / 输出 {usage['output_tokens']} tokens · 错误 {usage['errors'] or 0}")
            elif kind == 'error':
                busy = False; status.set('ChatGPT：' + result)
            else:
                busy = False
                if 'remote_revocation_confirmed' in result:
                    status.set('已断开并撤销授权。' if result['remote_revocation_confirmed'] else
                               '本机已断开；远端撤销未确认，请在 ChatGPT 设置中断开应用。')
                else:
                    status.set('已连接，仅显式合成调用会使用套餐。请在 Manage usage 中管理用量。')
        if not busy and ticks % 20 == 0:
            def refresh():
                try:
                    results.put(('status', (Credentials().status(), UsageLedger().snapshot())))
                except Exception as error:
                    results.put(('error', type(error).__name__))
            threading.Thread(target=refresh, daemon=True).start()
        ticks += 1
        panel.after(500, poll)
    poll()
    return panel
