"""Explicit, bounded live reading launcher; credentials never enter saved state."""
from pathlib import Path
import argparse
from decimal import Decimal
import json
import re
import sys
import threading
import urllib.request
import webbrowser

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from switchlab.memory.service import MemoryService
from switchlab.memory.http import create_server
from switchlab.studio.provider import Provider

MODEL='openai/gpt-5.4'
INPUT=Decimal('0.0000025')
OUTPUT=Decimal('0.000015')
CONFIG={'mode':'api','base_url':'https://openrouter.ai/api/v1','model':MODEL,
        'json_mode':True,'max_output_tokens':2400,'timeout':120,
        'token_parameter':'max_completion_tokens','network_consent':True,'max_calls':16}


def load_codex_key(path):
    lines=Path(path).read_text(encoding='utf-8-sig').splitlines()
    matches=[]
    for i,line in enumerate(lines):
        if 'codex' in line.casefold() and 'key' in line.casefold():
            candidates=re.findall(r'sk-or-[A-Za-z0-9_-]+',line)
            if not candidates and i+1<len(lines):
                candidates=re.findall(r'sk-or-[A-Za-z0-9_-]+',lines[i+1])
            matches.extend(candidates)
    if len(matches)!=1:raise ValueError('没有找到唯一的 codex key；没有使用文件里的其他密钥。')
    return matches[0]


def verify_price():
    with urllib.request.urlopen('https://openrouter.ai/api/v1/models',timeout=30) as r:
        models=json.load(r)['data']
    item=next((m for m in models if m['id']==MODEL),None)
    if not item:raise ValueError('预定模型当前不可用，没有付费请求。')
    price=item['pricing']
    if Decimal(price['prompt'])>INPUT or Decimal(price['completion'])>OUTPUT or Decimal(price.get('request','0'))!=0:
        raise ValueError('模型价格超出此次预算假设，没有付费请求。')


class BudgetProvider(Provider):
    def __init__(self,path,key,max_usd='1.00'):
        super().__init__(CONFIG,key)
        self.path=Path(path);self.budget_lock=threading.Lock()
        self.maximum=Decimal(max_usd)
        if not self.maximum.is_finite() or not 0<self.maximum<=1:raise ValueError('预算必须在 0 到 1 美元之间')

    def complete(self,messages):
        # Reserve before I/O; retain reservation on failures, invalid packets and
        # restart. Deliberately do not refund estimates based on missing usage.
        if self.config!=CONFIG:raise ValueError('有界验证固定模型和调用配置；请恢复启动配置。')
        with self.budget_lock:
            ledger=json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {'calls':0,'reserved_usd':'0'}
            estimate=(Decimal(len(json.dumps(messages,ensure_ascii=False).encode('utf-8'))+4096)*INPUT+Decimal(CONFIG['max_output_tokens'])*OUTPUT)*Decimal('1.1')
            reserved=Decimal(ledger['reserved_usd'])
            if ledger['calls']>=16 or reserved+estimate>self.maximum:
                raise ValueError('此次验证预算已到边界（最多16次、保守预留最多1美元）；没有发送新请求。')
            ledger.update(calls=ledger['calls']+1,reserved_usd=str(reserved+estimate),
                          max_usd=str(self.maximum),model=MODEL,accounting='conservative UTF-8 byte upper estimate; no refunds on errors')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(ledger,indent=2),encoding='utf-8');temp.replace(self.path)
        return super().complete(messages)


class BoundedService(MemoryService):
    def configure(self,data,key=None,clear_key=False):
        raise ValueError('当前为最多1美元的固定模型验证入口。连接设置由启动器提供，不能在页面绕过预算。')


def open_service(directory,key_file,checkpoint=None):
    directory=Path(directory)
    verify_price()
    provider=BudgetProvider(directory/'reading_budget.json',load_codex_key(key_file))
    s=BoundedService(directory,provider=provider)
    try:
        if checkpoint and s.store.sequence==0:
            s.import_checkpoint(json.loads(Path(checkpoint).read_text(encoding='utf-8-sig')))
        calls=s.store.setting('calls') or 0
        if s.call_ceiling()<calls+16 and not (directory/'reading_budget.json').exists():
            s.grant_calls(calls+16-s.call_ceiling())
        s.set_options({'language_mode':'api'})
        return s
    except BaseException:
        s.close();raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-file',required=True)
    parser.add_argument('--data-dir',default=str(ROOT/'user_data'/'reading_v07_final'))
    parser.add_argument('--checkpoint',help='Verified import only when the current life is empty')
    parser.add_argument('--port',type=int,default=8777)
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    service=open_service(args.data_dir,args.key_file,args.checkpoint)
    server=None
    try:
        server=create_server(service,args.port);service.start_worker()
        url=f'http://127.0.0.1:{server.server_port}/reading'
        print('SharedField v0.7 real reading: '+url,flush=True)
        print('Model: '+MODEL+'; persisted budget: <=16 calls / <=$1 conservative reservation.',flush=True)
        print('Starts paused. Key is process-only. Closing keeps the shared history.',flush=True)
        if not args.no_browser:webbrowser.open(url)
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:pass
    finally:
        if server:server.server_close()
        service.close()


if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError) as error:
        print('Start stopped: '+str(error),file=sys.stderr);sys.exit(1)
