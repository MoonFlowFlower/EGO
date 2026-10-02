"""Fresh-process probe of legacy/new implementations; only development RNG."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
from evolab.config import setup, generator
from evolab.es import OpenES

if sys.argv[1] == 'legacy':
    from evolab.config import Config
    from evolab.brains import Brain
    from evolab.rollout import rollout
else:
    from evolab.v002.config import Config
    from evolab.v002.brains import Brain
    from evolab.v002.rollout import rollout

setup()
arm = sys.argv[2]
c = replace(Config(), population=8, episodes=4, horizon=180, generations=5)
brain = Brain(arm, c)
es = OpenES(brain.initial_mean(generator(c.master_seed, 'init')), c)
records = []
for gen in range(c.generations):
    candidates = es.ask(generator(c.master_seed, gen, 'mutation'))
    scores, _ = rollout(c, 'drift', arm, c.episodes, 0, 'dev', gen, candidates, use_graph=True)
    es.tell(scores.mean(-1))
    records.append(scores.mean(-1).tolist())
Path(sys.argv[3]).write_text(json.dumps(dict(arm=arm, fitness=records, mean=es.mean.tolist())), encoding='utf-8')
