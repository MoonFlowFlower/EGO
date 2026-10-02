import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import json,time
import torch
from evolab.config import Config,setup,generator
from evolab.brains import Brain
from evolab.es import OpenES
from evolab.rollout import rollout

def train_short(arm='gru_fixed'):
    c=replace(Config(),population=8,episodes=4,horizon=180,generations=5)
    brain=Brain(arm,c); es=OpenES(brain.initial_mean(generator(c.master_seed,'init')),c)
    records=[]
    for gen in range(c.generations):
        candidates=es.ask(generator(c.master_seed,gen,'mutation'))
        scores,_=rollout(c,'drift',arm,c.episodes,0,'dev',gen,candidates,use_graph=True)
        es.tell(scores.mean(-1)); records.append(scores.mean(-1).tolist())
    return {'arm':arm,'fitness':records,'mean':es.mean.tolist()}

if __name__=='__main__':
    setup(); result=train_short(sys.argv[1] if len(sys.argv)>1 else 'gru_fixed')
    Path(sys.argv[2]).write_text(json.dumps(result),encoding='utf-8',newline='\n')
