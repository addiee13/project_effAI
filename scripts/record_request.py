#!/usr/bin/env python3
"""Portable real-prompt recorder for an already-running pinned server.

Useful for the Android handoff via `adb forward tcp:8088 tcp:8088`.
This command alone does not enforce thermal or repeat-gap gates; the Android
operator must satisfy and record those protocol gates before invoking it.
"""
import argparse
import json
from pathlib import Path
import time
import run_study as core

ap=argparse.ArgumentParser()
ap.add_argument('--url',default='http://127.0.0.1:8088')
ap.add_argument('--input',type=int,choices=[256,1024,2048],required=True)
ap.add_argument('--output',type=int,choices=[128,512],required=True)
ap.add_argument('--run-dir',type=Path,required=True)
ap.add_argument('--label',required=True,help='Unique Android configuration/run label')
args=ap.parse_args()
core.BASE=args.url
args.run_dir.mkdir(parents=True,exist_ok=False)
started=core.utc()
record={'schema_version':1,'label':args.label,'started_at':started,'device':'android','validation_status':'operator must attach device/thermal/power evidence; client utility is not a validated Android sweep','status':'starting'}
try:
    p=core.prompt(args.input,args.run_dir/'prompt.json',core.ROOT/'prompts/corpus-v1.txt')
    req={'prompt':p['tokens'],'n_predict':args.output,'temperature':0,'seed':113,'ignore_eos':True,'cache_prompt':False,'stream':True,'return_tokens':True,'timings_per_token':False}
    core.save(args.run_dir/'request.json',req)
    result=core.stream(req,args.run_dir/'stream.jsonl')
    final=result['final']
    if final['tokens_evaluated']!=args.input or final['tokens_predicted']!=args.output or final.get('truncated') or final['timings'].get('cache_n',0):
        raise RuntimeError('token occupancy/generation/cache validation failed')
    record.update(result);record['runtime_timings']=final['timings'];record['status']='ok'
except BaseException as exc:
    record['status']='failed';record['error']={'type':type(exc).__name__,'message':str(exc)}
    raise
finally:
    record['finished_at']=core.utc();core.save(args.run_dir/'result.json',record)
print(json.dumps({k:record[k] for k in ['label','status','request_wall_seconds','ttft_seconds','runtime_timings']}))
