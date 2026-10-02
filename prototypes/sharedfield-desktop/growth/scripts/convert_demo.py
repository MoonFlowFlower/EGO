import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.demonstration import convert
p=argparse.ArgumentParser();p.add_argument('npz');p.add_argument('sidecar');p.add_argument('output');a=p.parse_args()
print(convert(a.npz,a.sidecar,a.output))
