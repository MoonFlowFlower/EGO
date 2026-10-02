import sys, time, re, json
sys.path.insert(0, 'jaxlife/src')
import jax, jax.numpy as jnp
jax.tree_map = jax.tree_util.tree_map  # removed in modern JAX; shim for the 2024 code
src = open('jaxlife/src/main.py').read()
block = src[src.index('    config = {'):src.rindex('    now = str')]
class A: pass
args = A()
import argparse
p_src = src[src.index('parser = argparse'):src.index('def gui_loop')]
ns = {}
exec('import argparse\n' + p_src, ns)
args = ns['parser'].parse_args(sys.argv[2:])
cfg_ns = {'args': args}
exec('\n'.join(l[4:] for l in block.splitlines()), cfg_ns)
config = cfg_ns['config']
config['RETURN_WORLD_STATE'] = False
config['NUM_WORLD_STEPS'] = int(sys.argv[1])
from world.world import World
w = World(config)
s = w.initialize(jax.random.PRNGKey(0))
scan = jax.jit(lambda s: jax.lax.scan(w.step, s, None, config['NUM_WORLD_STEPS']))
t=time.time(); s, m = scan(s); jax.block_until_ready(s); t1=time.time()-t
s, m = scan(s); jax.block_until_ready(s)
t=time.time(); s, m = scan(s); jax.block_until_ready(s); t2=time.time()-t
n = config['NUM_WORLD_STEPS']
print(json.dumps(dict(agents=config['NUM_AGENTS'], bots=config['NUM_BOTS'], steps=n, compile_plus_run_s=round(t1,1), run_s=round(t2,2),
  world_steps_per_s=round(n/t2,1), agent_steps_per_s=round(n*config['NUM_AGENTS']/t2),
  alive_end=int(m['num_agents'][-1]), new_childs=int(m['num_new_childs'].sum()), new_random=int(m['num_new_random'].sum()))))
