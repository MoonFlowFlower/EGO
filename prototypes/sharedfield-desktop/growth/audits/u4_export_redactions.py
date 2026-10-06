"""Omit opaque encrypted response state, preserving every decision and request."""
import hashlib
import json

from u3.common import sha, write, utc
from u4.corpus import BASE, OUT, rows
from u4.run import verify


def export():
    verify()
    source = BASE / 'D2/calls.jsonl'
    target = OUT / 'raw/D2/calls.jsonl'
    records = rows(source)
    removed = []
    for line, record in enumerate(records, 1):
        if record['event'] != 'response' or not record.get('response'):
            continue
        for index, item in enumerate(record['response'].get('output', [])):
            if 'encrypted_content' not in item:
                continue
            value = item.pop('encrypted_content')
            if value is not None:
                assert isinstance(value, str)
                removed.append({'line': line, 'input_id': record['input_id'],
                    'path': f'response.output[{index}].encrypted_content',
                    'characters': len(value), 'sha256': hashlib.sha256(value.encode()).hexdigest()})
    with target.open('w', encoding='utf-8', newline='\n') as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + '\n')
    write(OUT / 'EXPORT_REDACTIONS.json', {'at_utc': utc(),
        'policy': 'Only encrypted_content fields in D2 response output items are omitted. '
                  'These opaque continuation-state fields are not credentials or decision text. '
                  'One ciphertext produced a token-pattern false positive. Requests, plaintext '
                  'output, usage, timestamps and error bodies are unchanged. Original capture '
                  'remains in ignored runs/. No inference is performed.',
        'source_capture_sha256': sha(source), 'exported_sha256': sha(target), 'removed': removed})
    print(json.dumps({'omitted_opaque_fields': len(removed), 'output': str(target)}))


if __name__ == '__main__':
    export()
