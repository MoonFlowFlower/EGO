"""自主项目 R2 的调用延迟复算（设计 v0.9 的 19.4）。用法：python initiative_r2_latency.py <growth 目录>

只读 runs/kernel_initiative_v1/paid_r2_*/<场景>/model.jsonl（负责人机器上 Codex 的工作树）。
输出每次调用的延迟、推理 token、输出 token 和每秒输出 token，以及延迟中位数。
"""
import statistics

from common import jsonl, root

g = root()
run = sorted((g / 'runs/kernel_initiative_v1').glob('paid_r2_*'))[-1]
latencies = []
for case in ('initial', 'transfer', 'masked', 'restored'):
    path = run / case / 'model.jsonl'
    if not path.exists():
        continue
    for r in jsonl(path):
        lat, out = r['latency_s'], r.get('output_tokens') or 0
        latencies.append(lat)
        print(f'{case:<9} 延迟 {lat:6.1f}s  推理 {r.get("reasoning_tokens")!s:>5}  输出 {out:>5}  '
              f'每秒输出 {out / lat:5.1f}  推理设置 {r.get("reasoning_requested")}')
print(f'\n共 {len(latencies)} 次，延迟中位数 {statistics.median(latencies):.1f}s，'
      f'最短 {min(latencies):.1f}s，最长 {max(latencies):.1f}s')
