import argparse,multiprocessing as mp,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.observatory import Mailbox,make_server
from growthlab.live_runner import run_live

def main():
    p=argparse.ArgumentParser();p.add_argument('--model');p.add_argument('--formal',action='store_true');p.add_argument('--port',type=int,default=8766)
    a=p.parse_args();ctx=mp.get_context('spawn');out=ctx.Queue(maxsize=1);controls=ctx.Queue(maxsize=16);stop=ctx.Event()
    process=ctx.Process(target=run_live,args=(out,controls,stop,a.model,a.formal));process.start()
    server=make_server(Mailbox(out),controls,a.formal,a.port)
    print(f'Owner-only http://127.0.0.1:{a.port}; simulator pid={process.pid}; formal={a.formal}',flush=True)
    try:server.serve_forever()
    finally:stop.set();process.join(3);server.server_close()
if __name__=='__main__':main()
