"""Owner recorder sidecar and fail-closed conversion, never read raw semantic values."""
import json
import time
import uuid
from pathlib import Path
import numpy as np
from .runtime import GrowthEnv
from .host import Host
from .contract import ACTIONS,validate
from .records import write_json


def recording_env(directory,source='owner_demonstration'):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    class RecordingEnv(GrowthEnv):
        def reset(self):
            image=super().reset()
            sensor=Host.__new__(Host);sensor.env=self;sensor.aliases={};sensor.actions=list(ACTIONS)
            sensor.done=False;sensor.world=uuid.uuid4().hex;sensor.delta=[0,0]
            self.sensor=sensor;self.sidecar={'source':source,'started_unix_s':time.time(),'complete':False,
                'initial':sensor.observe(),'transitions':[]}
            self.sidecar_path=directory/f'allowed_{sensor.world}.json';write_json(self.sidecar_path,self.sidecar)
            return image
        def step(self,action):
            before=self._player.pos.copy();result=super().step(action)
            self.sensor.done=bool(result[2]);self.sensor.delta=[int(x) for x in self._player.pos-before]
            self.sidecar['transitions'].append({'action':ACTIONS[action],'observation':self.sensor.observe()})
            self.sidecar['complete']=bool(result[2]);self.sidecar['duration_s']=time.time()-self.sidecar['started_unix_s']
            write_json(self.sidecar_path,self.sidecar)
            return result
    return RecordingEnv


def convert(npz,sidecar,output):
    allowed=json.loads(Path(sidecar).read_text(encoding='utf-8'))
    if not allowed['complete']:raise ValueError('incomplete_demonstration')
    with np.load(npz,allow_pickle=False) as raw:
        actions=raw['action'][1:].tolist();done=raw['done'].tolist()
        dropped=[x for x in raw.files if x not in ('action','done')]
    rows=allowed['transitions']
    if len(actions)!=len(rows) or not done[-1]:raise ValueError('raw_sidecar_mismatch')
    if [ACTIONS[x] for x in actions]!=[x['action'] for x in rows]:raise ValueError('action_alignment')
    clean={'schema':'growth.demo.v1','source':allowed['source'],'complete':True,
        'duration_s':allowed['duration_s'],'initial':validate(allowed['initial']),
        'transitions':[{'action':x['action'],'observation':validate(x['observation'])} for x in rows]}
    write_json(output,clean)
    return {'steps':len(rows),'dropped_raw_fields':dropped,'complete':True,'source':clean['source']}
