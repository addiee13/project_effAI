#!/usr/bin/env python3
"""Download immutable official GGUF files outside Git and verify SHA-256."""
import argparse, hashlib, json, pathlib, subprocess

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',type=pathlib.Path,default=pathlib.Path.home()/'.cache/effai/models');a=p.parse_args()
    a.directory.mkdir(parents=True,exist_ok=True)
    models=json.loads((pathlib.Path(__file__).resolve().parents[1]/'configs/models.json').read_text())
    for m in models:
        dst=a.directory/m['filename']
        if not dst.exists() or sha256(dst)!=m['sha256']:
            tmp=dst.with_suffix('.part')
            subprocess.run(['curl','--fail','--location','--retry','2','--connect-timeout','30','--max-time','1800',m['url'],'-o',str(tmp)],check=True)
            if sha256(tmp)!=m['sha256']: raise ValueError(f'Checksum mismatch: {tmp}')
            tmp.replace(dst)
        print(m['id'],dst,sha256(dst),flush=True)
if __name__=='__main__': main()
