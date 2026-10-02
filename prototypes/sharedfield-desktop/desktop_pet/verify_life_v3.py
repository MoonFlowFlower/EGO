"""One-shot two-request diagnostic. Synthetic state only; refuse replay."""
import hashlib
import json
from pathlib import Path
from .life import Life
from . import dialogue

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'evidence/life-sharing-v3-20260926'


def save(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=False)
    files=['life.py','dialogue.py','letter_content.py','server.py','web/app.js','web/style.css','verify_life_v3.py']
    save('manifest.json',{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
    original=dialogue.generate;calls=0;case=''
    def recorded(life,messages,purpose):
        nonlocal calls
        if calls>=2:raise RuntimeError('two request diagnostic limit')
        calls+=1;save(case+'-prompt.json',messages)
        return original(life,messages,purpose)
    dialogue.generate=recorded
    dialogue.ORDER=['qwen35']  # No hidden or 429 model fallback in this diagnostic.
    life=Life(OUT/'data',enable_life_sharing=True)
    try:
        for case in ('autonomous-eat','invited-rest'):
            if case=='autonomous-eat':
                life.command('teach',request_id=case)
                life.advance(1)
                for _ in range(8):life.advance(2)
            else:
                life.command('rest',request_id=case)
                for _ in range(13):life.advance(2)
            life.command('write',request_id=case+'-write')
            for _ in range(10):life.advance(2)
            job=life.claim_letter_job()
            if not job:raise RuntimeError('missing completed action job')
            save(case+'-fixture.json',job)
            result=dialogue.compose_letter(life,job)
            save(case+'-raw-output.json',result)
            life.finish_letter_job(job['id'],text=result)
            save(case+'-letter.json',life.snapshot()['letters'][-1])
        with life.db() as db:receipts=[json.loads(r[0]) for r in db.execute('SELECT value FROM calls')]
        save('receipts.json',receipts)
        save('result.json',{'status':'awaiting_content_and_ui_review','requests':len(receipts),
                           'known_cost_usd':sum((r.get('usage') or {}).get('cost',0) for r in receipts),
                           'letters':life.snapshot()['letters']})
        print(json.dumps({'requests':len(receipts),'letters':life.snapshot()['letters']},ensure_ascii=False))
    except Exception as exc:
        save('STOPPED.json',{'case':case,'error_type':type(exc).__name__,'requests_attempted':calls})
        raise


if __name__=='__main__':main()
