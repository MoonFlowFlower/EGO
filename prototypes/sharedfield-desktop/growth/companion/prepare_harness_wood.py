"""Owner-authorized bounded material preparation; no model, no building."""
import json
import time
import argparse
from .body import Body, ROOT
from p7.proxy import AuditLog


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--oak-only',action='store_true');args=parser.parse_args()
    preparation='oak_preparation' if args.oak_only else 'tree_preparation'
    base=ROOT/'runs/kernel_harness_v2';base.mkdir(parents=True,exist_ok=True)
    with (base/(preparation+'.claim')).open('x',encoding='utf-8') as f:f.write(str(time.time_ns()))
    folder=base/preparation;audit=AuditLog(folder,());body=Body(audit)
    result={'model_calls':0,'receipts':[],'passed':False}
    try:
        body.start();deadline=time.monotonic()+30
        while body.snapshot().get('offline') and time.monotonic()<deadline:time.sleep(.2)
        result['before']=body.snapshot()
        if result['before'].get('offline'):raise RuntimeError('body_not_ready')
        body.say('工程检查准备：只从带树干和叶冠的树上取一块原木，不动地基；随后回到你身边。')
        for action in ({'name':'recover_inventory','args':{}},{'name':'collect_tree','args':{'block':'oak_log' if args.oak_only else 'wood','range':128}}):
            receipt=body.start_action(action).result(timeout=65)
            result['receipts'].append({'action':action,'receipt':receipt})
            if not receipt.get('verified'):break
        else:
            result['passed']=True
            # Return using official approach; no harvesting follows this point.
            receipt=body.start_action({'name':'approach','args':{}}).result(timeout=65)
            result['receipts'].append({'action':{'name':'approach','args':{}},'receipt':receipt})
        result['after']=body.snapshot()
    except Exception as e:result['error_type']=type(e).__name__
    finally:
        body.close('tree_preparation_finished')
        result['body_exit_code']=body.process.poll() if body.process else None
        folder.mkdir(parents=True,exist_ok=True)
        (folder/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
