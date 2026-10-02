"""Double-click launch without a terminal window. Uses the installed Edge host."""
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT=Path(__file__).resolve().parent
URL='http://127.0.0.1:18180'

def ready():
    try:
        with urllib.request.urlopen(URL+'/api/health',timeout=1) as r:return b'ego-desktop-pet' in r.read()
    except Exception:return False

if not ready():
    logdir=ROOT/'data';logdir.mkdir(exist_ok=True)
    with (logdir/'server.log').open('ab') as log:
        subprocess.Popen([sys.executable,'-B','-m','desktop_pet.server'],cwd=ROOT.parent,
                         stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    for _ in range(35):
        if ready():break
        time.sleep(.2)
if ready():
    browsers=[Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'),Path('C:/Program Files/Google/Chrome/Application/chrome.exe')]
    browser=next((p for p in browsers if p.exists()),None)
    if browser:
        subprocess.Popen([str(browser),'--app='+URL,'--window-size=1180,920',
                          '--user-data-dir='+str(ROOT/'data/window-profile'),'--no-first-run','--no-default-browser-check'])
    else:webbrowser.open(URL)
else:
    import ctypes
    ctypes.windll.user32.MessageBoxW(0,'小屋没能启动，请查看 desktop_pet/data/server.log。','悠小喵的小屋',0)
