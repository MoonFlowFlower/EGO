"""Lossless spatial compression and exact-alias removal for model input only."""
import copy
from collections import defaultdict


def regions(cells):
    """Merge contiguous x, z and y runs. Never infer an unobserved cell."""
    rows=defaultdict(set)
    for x,y,z,block in cells:rows[(y,z,block)].add(x)
    x_runs=[]
    for (y,z,block),xs in rows.items():
        lo=hi=None
        for x in sorted(xs):
            if hi is not None and x==hi+1:hi=x
            else:
                if hi is not None:x_runs.append((lo,hi,y,z,block))
                lo=hi=x
        if hi is not None:x_runs.append((lo,hi,y,z,block))
    planes=defaultdict(set)
    for x0,x1,y,z,block in x_runs:planes[(x0,x1,y,block)].add(z)
    z_runs=[]
    for (x0,x1,y,block),zs in planes.items():
        lo=hi=None
        for z in sorted(zs):
            if hi is not None and z==hi+1:hi=z
            else:
                if hi is not None:z_runs.append((x0,x1,y,lo,hi,block))
                lo=hi=z
        if hi is not None:z_runs.append((x0,x1,y,lo,hi,block))
    volumes=defaultdict(set)
    for x0,x1,y,z0,z1,block in z_runs:volumes[(x0,x1,z0,z1,block)].add(y)
    result=[]
    for (x0,x1,z0,z1,block),ys in volumes.items():
        def add(a,b):result.append({'min':{'x':x0,'y':a,'z':z0},'max':{'x':x1,'y':b,'z':z1},'block':block})
        lo=hi=None
        for y in sorted(ys):
            if hi is not None and y==hi+1:hi=y
            else:
                if hi is not None:add(lo,hi)
                lo=hi=y
        if hi is not None:add(lo,hi)
    return sorted(result,key=lambda r:(r['min']['y'],r['min']['z'],r['min']['x'],str(r['block'])))


def valid_point(p):return isinstance(p,dict) and set(p)=={'x','y','z'} and all(type(v) is int for v in p.values())


def project(value):
    if isinstance(value,list):return [project(v) for v in value]
    if not isinstance(value,dict):return value
    result={k:project(v) for k,v in value.items()}
    points=value.get('positions')
    if value.get('kind')=='blocks' and isinstance(points,list) and points and all(valid_point(p) for p in points):
        if len({tuple(p[k] for k in ('x','y','z')) for p in points})==len(points):
            result.pop('positions');result['regions']=[{k:v for k,v in r.items() if k!='block'}
                for r in regions([[p['x'],p['y'],p['z'],value['block']] for p in points])]
    cells=value.get('cells')
    if isinstance(cells,list) and cells and all(isinstance(c,list) and len(c)==4 and all(type(v) is int for v in c[:3])
            and (c[3] is None or isinstance(c[3],str)) for c in cells) and len({tuple(c[:3]) for c in cells})==len(cells):
        result.pop('cells');result.update(observed_regions=regions(cells),observed_cell_count=len(cells),
            spatial_encoding='inclusive integer xyz regions; null=unknown, air=observed empty; outside these regions is not observed')
    blocks=value.get('blocks')
    if value.get('status')=='goal_blocks_checked' and isinstance(blocks,list) and blocks and all(isinstance(b,dict)
            and set(b)=={'block','position','observed_block','matches'} and valid_point(b['position']) for b in blocks):
        grouped=defaultdict(list)
        for b in blocks:
            p=b['position'];grouped[(b['block'],b['observed_block'],b['matches'])].append([p['x'],p['y'],p['z'],b['observed_block']])
        result.pop('blocks');result['block_checks']=[{'expected':wanted,'observed':observed,'matches':matches,
            'positions_count':len(cells),'regions':[{k:v for k,v in r.items() if k!='block'} for r in regions(cells)]}
            for (wanted,observed,matches),cells in grouped.items()]
    return result


def compact_context(context):
    result=copy.deepcopy(context)
    feedback=result.get('execution_feedback')
    if isinstance(feedback,dict):
        for source,target in (('current_body','body'),('work','work')):
            if source in feedback and target in result and feedback[source]==result[target]:
                feedback.pop(source);feedback[source+'_ref']='context.'+target
        if feedback.get('receipts')==result.get('receipts'):result.pop('receipts',None)
        if 'harness_notice' in result and feedback.get('harness_notice')==result['harness_notice']:
            result.pop('harness_notice')
    goal=result.get('goal');work=result.get('work')
    if isinstance(goal,dict) and work is not None and goal.get('work')==work:
        goal.pop('work');goal['work_ref']='context.work'
    if isinstance(work,dict) and result.get('original_request')==work.get('request'):
        result['original_request']={'ref':'context.work.request'}
    return project(result)
