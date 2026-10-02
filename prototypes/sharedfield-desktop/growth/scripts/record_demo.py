"""Launch pinned upstream run_gui --record with P8 fixes and a P1 sidecar."""
import argparse,runpy,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crafter
from growthlab.demonstration import recording_env
from growthlab.records import RUNS
p=argparse.ArgumentParser();p.add_argument('--directory');a=p.parse_args()
directory=Path(a.directory) if a.directory else RUNS/('owner_demo_'+time.strftime('%Y%m%d_%H%M%S'))
crafter.Env=recording_env(directory)
sys.argv=['crafter.run_gui','--record',str(directory),'--seed','11','--length','180',
          '--fps','5','--wait','True','--death','quit','--window','600','600']
print('Local recording directory:',directory,flush=True)
runpy.run_module('crafter.run_gui',run_name='__main__')
