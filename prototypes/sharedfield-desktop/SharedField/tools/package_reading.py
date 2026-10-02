"""Build/verify a source delivery without personal data or runtime outputs."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'user_data','outputs','.git','__pycache__'}
GENERATED={'MANIFEST.sha256','evidence_v07/package_verification.json'}


def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file()
                  and not EXCLUDED.intersection(p.relative_to(ROOT).parts)
                  and p.suffix not in ('.pyc','.lock')
                  and p.relative_to(ROOT).as_posix() not in GENERATED)


def verify():
    manifest=ROOT/'MANIFEST.sha256'
    entries={line.split('  ',1)[1]:line.split('  ',1)[0] for line in manifest.read_text(encoding='utf-8').splitlines()}
    actual={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files()}
    if entries!=actual:raise ValueError('Manifest content or file inventory differs')
    return len(actual)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--build',type=Path)
    args=parser.parse_args()
    if args.build:
        target=args.build.resolve()
        if target.is_relative_to(ROOT):raise ValueError('Write the ZIP outside the source directory')
        paths=files()
        (ROOT/'MANIFEST.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in paths),encoding='utf-8')
        count=verify()
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
            for p in paths+[ROOT/'MANIFEST.sha256']:z.write(p,'SharedField/'+p.relative_to(ROOT).as_posix())
        with zipfile.ZipFile(target) as z:
            if z.testzip():raise ValueError('ZIP CRC failed')
            for p in paths:
                assert z.read('SharedField/'+p.relative_to(ROOT).as_posix())==p.read_bytes()
        report={'files':count,'manifest_verified':True,'zip_bytes_verified':True,
                'personal_data_included':False,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
        (ROOT/'evidence_v07/package_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report))
    elif args.verify:print(json.dumps({'manifest_verified':True,'files':verify()}))
    else:parser.error('Choose --verify or --build PATH')


if __name__=='__main__':main()
