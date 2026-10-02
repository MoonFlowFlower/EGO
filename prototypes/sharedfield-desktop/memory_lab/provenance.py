"""Record exact upstream revisions, licenses and dependency locks without credentials."""
import hashlib
import json
import shutil
import subprocess
from .provider import ROOT, write_json

PINS={'hindsight':'f8950b0c07d9e34c76493dba802bb309f0ce60fd',
      'MemOS':'a7367d07e55db61099f7b4e2c1108bc5831a24f3','ace':'82709de050e1db6e6ef2f07bcb0393560b94992a'}
URLS={'hindsight':'https://github.com/vectorize-io/hindsight',
      'MemOS':'https://github.com/MemTensor/MemOS','ace':'https://github.com/ace-agent/ace'}

def main():
    licenses=ROOT/'licenses';licenses.mkdir(exist_ok=True)
    manifest={}
    for name,commit in PINS.items():
        path=ROOT/'vendor'/name
        head=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
        if head!=commit:raise ValueError('Upstream revision changed: '+name)
        remote=subprocess.check_output(['git','-C',str(path),'remote','get-url','origin'],text=True).strip()
        manifest[name]={'commit':head,'repository':remote,'licenses':[]}
        for file in path.glob('*'):
            if file.is_file() and ('LICENSE' in file.name.upper() or 'NOTICE' in file.name.upper()):
                dst=licenses/(name+'-'+file.name);shutil.copyfile(file,dst)
                manifest[name]['licenses'].append({'file':str(dst.relative_to(ROOT)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
    plugin=ROOT/'vendor/MemOS/apps/memos-local-openclaw'
    for file in plugin.glob('*LICENSE*'):
        dst=licenses/('MemOS-local-'+file.name);shutil.copyfile(file,dst)
        manifest['MemOS']['licenses'].append({'file':str(dst.relative_to(ROOT)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()})
    shutil.copyfile(plugin/'package-lock.json',ROOT/'memos-package-lock.json')
    shutil.copyfile(plugin/'package.json',ROOT/'memos-package.json')
    manifest['retrieval_models']=json.loads((ROOT/'model-revisions.json').read_text())
    for name in ('bge-m3','bge-reranker-v2-m3'):
        path=ROOT/'.cache/models'/name
        # Upstream model card carries its license metadata; immutable revision used for retrieval.
        revision=manifest['retrieval_models']['BAAI/'+name]
        import urllib.request
        with urllib.request.urlopen(f'https://huggingface.co/BAAI/{name}/resolve/{revision}/README.md') as r:
            (licenses/(name+'-MODEL_CARD.md')).write_bytes(r.read())
    manifest['configuration']={'model':'deepseek/deepseek-v4-flash-0731','provider_only':['deepinfra/fp8'],
         'fallbacks':False,'temperature':0,'top_p':1,'seed':20260923,'reasoning':False,
         'paid_request_retries':0,'paid_call_limit':5000,'cpu_embedding':True,
         'embedding_sequence_cap':2048,'reranker_sequence_cap':2048}
    write_json(ROOT/'upstream-lock.json',manifest)
    print('Upstream commits, licenses, model revisions and npm lock saved.')

if __name__=='__main__':main()
