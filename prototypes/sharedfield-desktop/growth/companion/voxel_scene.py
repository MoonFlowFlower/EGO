"""Isolated voxel observation/action fixture; no building layout or model inside.

Models a loaded flat world, inventory, adjacent supports and walkable cells.
Minecraft packets, ray casting, gravity and server navigation need live evidence.
"""
import concurrent.futures
import copy
import math
import time
from collections import deque


XYZ=('x','y','z')
def xyz(p):return tuple(p[k] for k in XYZ)
def point(p):return dict(zip(XYZ,p))


class VoxelScene:
    def __init__(self, *, origin=(12,70,-8), inventory=None, loaded=True, occupied=False):
        self.origin=origin;self.floor=origin[1]-1;self.loaded=loaded
        self.blocks={};self.actions=[];self.speech=[];self.cancelled=False;self.changes=[]
        self.state={'offline':False,'position':point(origin),'inventory':dict(oak_planks=128) if inventory is None else inventory.copy(),
            'crafting_grid':{},'cursor':None,'window':None,'health':20,
            'owner':{'name':'Moonlight','position':point((origin[0]+2,origin[1],origin[2])), 'distance':2,'height_difference':0},
            'dropped_items':{'items':[],'scope':'loaded_entities_only'},'recent_pickups':[]}
        if occupied:
            for x in range(origin[0]-4,origin[0]+5):
                for z in range(origin[2]-4,origin[2]+5):
                    for y in range(origin[1],origin[1]+3):
                        if (x,z)!=(origin[0],origin[2]):self.blocks[(x,y,z)]='stone'
        self.initial_blocks=copy.deepcopy(self.blocks);self.initial_inventory=self.state['inventory'].copy()

    def block(self,p):
        if not self.loaded or abs(p[0]-self.origin[0])>24 or abs(p[2]-self.origin[2])>24:return None
        return self.blocks.get(p,'stone' if p[1]<=self.floor else 'air')

    def snapshot(self):
        value=copy.deepcopy(self.state);value['sampled_at']=time.time()*1000
        a,b=xyz(value['position']),xyz(value['owner']['position'])
        value['owner'].update(distance=math.dist(a,b),height_difference=abs(a[1]-b[1]))
        return value

    def say(self,text):self.speech.append(text)
    def stop(self):self.cancelled=True;return {'verified':True,'status':'stopped'}

    def standable(self,p):
        return self.block(p)=='air' and self.block((p[0],p[1]+1,p[2]))=='air' and self.block((p[0],p[1]-1,p[2])) not in (None,'air')

    def reach(self,target,distance=4.5):
        # Walk only through currently supported free cells; cannot dig or scaffold.
        start=xyz(self.state['position']);queue=deque([start]);seen={start}
        while queue and len(seen)<=4096:
            p=queue.popleft()
            if math.dist(p,target)<=distance and target not in (p,(p[0],p[1]+1,p[2])):
                self.state['position']=point(p);return True
            for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
                for dy in (0,1,-1):
                    nxt=(p[0]+dx,p[1]+dy,p[2]+dz)
                    if nxt not in seen and self.standable(nxt):seen.add(nxt);queue.append(nxt)
        return False

    def place(self,target):
        p=xyz(target['position']);block=target['block'];before=self.state['inventory'].get(block,0)
        status=None
        if self.cancelled:status='interrupted'
        elif math.dist(xyz(self.state['position']),p)>16:status='target_out_of_reach'
        elif self.block(p) is None:status='target_not_loaded'
        elif self.block(p)!='air':status='placement_target_not_empty'
        elif before<1:status='placement_material_missing'
        elif not self.reach(p):status='placement_path_failed'
        elif not any(self.block(tuple(p[i]+offset[i] for i in range(3))) not in (None,'air')
                     for offset in ((0,-1,0),(0,1,0),(0,0,-1),(0,0,1),(1,0,0),(-1,0,0))):status='placement_no_support'
        if status:return {'verified':False,'status':status,'position':target['position']}
        self.blocks[p]=block;self.state['inventory'][block]=before-1;self.changes.append(copy.deepcopy(target))
        return {'verified':True,'status':'placed_block_checked','position':target['position'],
            'placement':{'before_block':'air','after_block':block,'inventory_before':before,'inventory_after':before-1,'consumed':1}}

    def start_action(self,action,**kwargs):
        self.actions.append(copy.deepcopy(action));name,args=action['name'],action['args']
        r={'verified':True,'status':'observed'}
        if name=='inspect_area':
            c=xyz(self.state['position']);radius=args['radius']
            cells=[[x,y,z,self.block((x,y,z))] for x in range(c[0]-radius,c[0]+radius+1)
                   for z in range(c[2]-radius,c[2]+radius+1) for y in range(c[1]-1,c[1]+3)]
            r.update(status='local_area_observed',scope='loaded_chunks_only',center=point(c),cells=cells)
        elif name=='verify_blocks':
            blocks=[{**t,'observed_block':self.block(xyz(t['position'])), 'matches':self.block(xyz(t['position']))==t['block']} for t in args['targets']]
            r.update(verified=bool(blocks) and all(t['matches'] for t in blocks),status='goal_blocks_checked',blocks=blocks)
        elif name=='approach':
            success=self.reach(xyz(self.state['owner']['position']),1.5)
            r.update(verified=success,status='approach_checked',navigation='no_break_no_place')
        elif name=='place_at':r=self.place(args)
        elif name=='place_many':
            receipts=[]
            for t in args['targets']:
                if self.cancelled:r={'verified':False,'status':'interrupted','placements':receipts};break
                child={'verified':True,'status':'target_already_matches','position':t['position']} if self.block(xyz(t['position']))==t['block'] else self.place(t)
                receipts.append({'target':t,'receipt':child})
                if not child['verified']:
                    r={'verified':False,'status':'placement_batch_partial','problem':child['status'],'placements':receipts};break
            else:r={'verified':True,'status':'placement_batch_checked','placements':receipts}
        elif name=='search':
            found=next((p for p,b in self.blocks.items() if b==args['block'] and math.dist(p,xyz(self.state['position']))<=args['range']),None)
            r.update(status='block_search_completed',found=found is not None,block_position=point(found) if found else None,matched_block=args['block'] if found else None)
        elif name=='craft':
            item=args['item'];log=item.removesuffix('_planks')+'_log';count=args['count']
            if item.endswith('_planks') and self.state['inventory'].get(log,0)>=count:
                self.state['inventory'][log]-=count;self.state['inventory'][item]=self.state['inventory'].get(item,0)+count*4
                r.update(status='craft_inventory_checked',gained=count*4)
            else:r.update(verified=False,status='missing_ingredients',missing_options=[{log:count}],available_plank_alternatives=[])
        elif name=='observe_items':r.update(status='items_observed',items=[])
        elif name!='inspect':r.update(verified=False,status='unsupported_fixture_action')
        r['observed']=self.snapshot();f=concurrent.futures.Future();f.set_result(r);return f

    def export(self):
        return {'blocks':[{'position':point(p),'block':b} for p,b in sorted(self.blocks.items())],
                'initial_inventory':self.initial_inventory,'state':self.snapshot(),'actions':self.actions,'changes':self.changes}


def grade_hut(scene):
    """Independent acceptance observer. It is never passed to the model."""
    wood={p for p,b in scene.blocks.items() if b.endswith('_planks') and p not in scene.initial_blocks}
    if not wood:return {'passed':False,'reason':'no_wood_structure'}
    lo=tuple(min(p[i] for p in wood) for i in range(3));hi=tuple(max(p[i] for p in wood) for i in range(3))
    result={'bounds':[list(lo),list(hi)],'wood_blocks':len(wood),'footprint_5x5':hi[0]-lo[0]==4 and hi[2]-lo[2]==4}
    roof=hi[1];base=scene.floor+1
    if all((x,base,z) in wood for x in range(lo[0],hi[0]+1) for z in range(lo[2],hi[2]+1)):base+=1
    result['roof']=all((x,roof,z) in wood for x in range(lo[0],hi[0]+1) for z in range(lo[2],hi[2]+1))
    result['interior_clear']=roof-base>=2 and all(scene.block((x,y,z))=='air'
        for x in range(lo[0]+1,hi[0]) for z in range(lo[2]+1,hi[2]) for y in range(base,roof))
    perimeter={(x,z) for x in range(lo[0],hi[0]+1) for z in range(lo[2],hi[2]+1)
               if x in (lo[0],hi[0]) or z in (lo[2],hi[2])}
    entrances=[];walls=True
    for x,z in perimeter:
        column=[scene.block((x,y,z)) for y in range(base,roof)]
        corner=x in (lo[0],hi[0]) and z in (lo[2],hi[2])
        if len(column)>=2 and column[:2]==['air','air'] and not corner:
            direction=(-1,0) if x==lo[0] else (1,0) if x==hi[0] else (0,-1) if z==lo[2] else (0,1)
            out=(x+direction[0],base,z+direction[1])
            if scene.standable(out):entrances.append([x,base,z])
            if any(v!='air' and not v.endswith('_planks') for v in column):walls=False
        elif not all(v and v.endswith('_planks') for v in column):walls=False
    result.update(walls=walls,entrances=entrances,entrance=bool(entrances) and len(entrances)<=2)
    result['materials_conserved']=all(scene.initial_inventory.get(b,0)-scene.state['inventory'].get(b,0)==sum(c['block']==b for c in scene.changes)
                                      for b in set(scene.initial_inventory)|set(scene.state['inventory']))
    result['existing_preserved']=all(scene.blocks.get(p)==b for p,b in scene.initial_blocks.items())
    result['passed']=all(result[k] for k in ('footprint_5x5','roof','interior_clear','walls','entrance','materials_conserved','existing_preserved'))
    return result
