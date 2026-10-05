"""Search fixture follows production receipt semantics and its actual block view."""
import copy
import math
from concurrent.futures import Future
from . import verify_blocked_v11 as acceptance
from .voxel_scene import point, xyz

WOOD_TYPES=('oak','spruce','birch','jungle','acacia','dark_oak','mangrove','cherry')


def search_view(scene,requested,distance):
    """Exhaust the fixture's loaded world within the requested sphere."""
    names=[kind+'_log' for kind in WOOD_TYPES] if requested=='wood' else [requested]
    center=xyz(scene.state['position']);cx,cy,cz=center;ox,_,oz=scene.origin
    nearest=None;best=distance*distance+1
    for x in range(max(ox-24,math.ceil(cx-distance)),min(ox+24,math.floor(cx+distance))+1):
        for z in range(max(oz-24,math.ceil(cz-distance)),min(oz+24,math.floor(cz+distance))+1):
            horizontal=(x-cx)**2+(z-cz)**2
            if horizontal>distance*distance:continue
            for y in range(max(-64,math.ceil(cy-distance)),min(319,math.floor(cy+distance))+1):
                squared=horizontal+(y-cy)**2
                if squared>distance*distance or squared>=best:continue
                p=(x,y,z);name=scene.block(p)
                if name in names:nearest=(p,name);best=squared
    return {'verified':nearest is not None,'status':'block_located' if nearest else 'block_not_found',
            'observation_complete':True,'found':nearest is not None,
            'query':{'requested':requested,'block_types':names,'range':distance,'scope':'loaded_chunks_only','center':point(center)},
            'matched_block':nearest[1] if nearest else None,'block_position':point(nearest[0]) if nearest else None,
            'distance':math.sqrt(best) if nearest else None}


class ConsistentSealedScene(acceptance.SealedScene):
    def start_action(self,action,**kwargs):
        if action['name']!='search':return super().start_action(action,**kwargs)
        self.actions.append(copy.deepcopy(action))
        receipt={**search_view(self,action['args']['block'],action['args']['range']),'observed':self.snapshot()}
        future=Future();future.set_result(receipt);return future


def main():
    acceptance.SealedScene=ConsistentSealedScene
    acceptance.EVIDENCE=acceptance.base.ROOT/'evidence/kernel_blocked_v12'
    acceptance.base.EVIDENCE=acceptance.EVIDENCE
    return acceptance.main()


if __name__=='__main__':raise SystemExit(main())
