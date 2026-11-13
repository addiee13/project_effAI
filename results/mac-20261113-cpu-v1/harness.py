#!/usr/bin/env python3
"""Pinned, serial llama.cpp real-prompt experiment. Python standard library only.

Each immutable run directory is the transaction boundary; result.json is written
atomically after raw events. A flock prevents concurrent studies. Failed and
interrupted attempts remain evidence and are retried under a new attempt ID.
"""
import argparse
import collections
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '79967ec596c0dacfd2251b085a57e79df292b1cc'
RUNTIME = Path(os.environ.get('EFFAI_RUNTIME_DIR', Path.home()/'.cache/effai/runtime')) / ('llama.cpp-'+COMMIT)
BIN = RUNTIME/'build-cpu/bin'
MODEL_DIR = Path(os.environ.get('EFFAI_MODEL_DIR', Path.home()/'.cache/effai/models'))
BASE = 'http://127.0.0.1:8088'
STOP = threading.Event()
SERVER = {}

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def sha(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def save(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)

def cmd(argv, timeout=15):
    p = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    return {'argv':argv, 'returncode':p.returncode, 'stdout':p.stdout, 'stderr':p.stderr}

def post(path, data, timeout=1800):
    req = urllib.request.Request(BASE+path, json.dumps(data).encode(), {'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)

def log(message):
    print(utc(), message, flush=True)

class Sensor:
    """Rootless macmon samples; raw values retained without invented units."""
    def __init__(self, path):
        self.path = path
        self.samples = collections.deque(maxlen=7200)
        self.lock = threading.Lock()
        self.proc = None
    def start(self):
        self.proc = subprocess.Popen(['/opt/homebrew/bin/macmon','pipe','--soc-info','--interval','1000'],stdout=subprocess.PIPE,stderr=open(self.path.with_suffix('.stderr.txt'),'a'),text=True,bufsize=1)
        self.thread = threading.Thread(target=self.read,daemon=True)
        self.thread.start()
    def read(self):
        with open(self.path,'a',buffering=1) as f:
            for line in self.proc.stdout:
                try:
                    sample=json.loads(line)
                    sample['received_unix']=time.time()
                    sample['received_monotonic']=time.monotonic()
                except Exception:
                    continue
                f.write(json.dumps(sample)+'\n')
                with self.lock: self.samples.append(sample)
    def window(self, seconds=60):
        now=time.monotonic()
        with self.lock: return [x for x in self.samples if now-x['received_monotonic']<=seconds]
    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=10)
            self.proc=None

def thermal(sensor, baseline, study, evidence, earliest=0):
    rule=study['thermal_rule']; start=time.monotonic()
    records=[]
    while not STOP.is_set():
        w=sensor.window(rule['window_seconds'])
        vals=[x['temp']['cpu_temp_avg'] for x in w if x.get('temp',{}).get('cpu_temp_avg') is not None]
        coverage=w[-1]['received_monotonic']-w[0]['received_monotonic'] if len(w)>1 else 0
        assessment={'at':utc(),'wait_seconds':time.monotonic()-start,'sample_count':len(vals),'coverage_seconds':coverage,'minimum':min(vals) if vals else None,'maximum':max(vals) if vals else None,'mean':statistics.mean(vals) if vals else None,'idle_baseline_celsius':baseline,'repeat_gap_satisfied':time.time()>=earliest,'cpu_active_ratio_mean':statistics.mean(x['cpu_active_ratio'] for x in w) if w else None,'cpu_power_w_mean':statistics.mean(x['cpu_power'] for x in w) if w else None}
        stable=coverage>=rule['window_seconds']-3 and len(vals)>=rule['window_seconds']-5 and max(vals)-min(vals)<=rule['maximum_range_celsius'] if vals else False
        cool=baseline is None or statistics.mean(vals)<=baseline+rule['maximum_above_idle_celsius'] if vals else False
        quiet=baseline is not None or (assessment['cpu_active_ratio_mean'] is not None and assessment['cpu_active_ratio_mean']<=study['idle_rule']['maximum_mean_cpu_active_ratio'] and assessment['cpu_power_w_mean']<=study['idle_rule']['maximum_mean_cpu_power_w'])
        assessment['idle_activity_rule_satisfied']=quiet
        assessment['accepted']=bool(stable and cool and quiet and assessment['repeat_gap_satisfied'])
        records.append(assessment); save(evidence,records)
        if assessment['accepted']: return assessment
        if time.monotonic()-start>rule['timeout_seconds']:
            raise RuntimeError('thermal stabilization timeout; no valid run scheduled')
        STOP.wait(rule['sample_interval_seconds'])
    raise InterruptedError('stop requested during thermal wait')

def prompt(n, path, corpus_path):
    """Template first, then crop only the corpus token region to exact occupancy."""
    corpus=corpus_path.read_text()
    body='Explain and summarize the following technical passage in detail. Continue until the requested generation limit.\n'+corpus*20
    formatted=post('/apply-template',{'messages':[{'role':'system','content':'You are a helpful assistant.'},{'role':'user','content':body}]})['prompt']
    toks=post('/tokenize',{'content':formatted,'add_special':True,'parse_special':True})['tokens']
    # The terminal assistant-generation prefix is retained intact. Its exact token
    # IDs are checked by detokenization and full-text re-tokenization below.
    ending='<|im_end|>\n<|im_start|>assistant\n'
    suffix=post('/tokenize',{'content':ending,'add_special':False,'parse_special':True})['tokens']
    assert toks[-len(suffix):]==suffix
    tokens=toks[:n-len(suffix)]+suffix
    text=post('/detokenize',{'tokens':tokens})['content']
    check=post('/tokenize',{'content':text,'add_special':True,'parse_special':True})['tokens']
    if check!=tokens: raise RuntimeError('formatted prompt token roundtrip mismatch')
    record={'schema_version':1,'input_tokens':len(tokens),'tokens':tokens,'text':text,'construction':'model apply-template, crop corpus tokens, preserve complete chat suffix; exact text roundtrip verified','corpus_sha256':sha(corpus_path)}
    save(path,record)
    return record

def stream(request, path):
    t0=time.monotonic(); start_unix=time.time(); events=[]; final=None
    req=urllib.request.Request(BASE+'/completion',json.dumps(request).encode(),{'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=1800) as response,open(path,'w',buffering=1) as f:
        for line in response:
            received=time.monotonic()
            if not line.startswith(b'data: '): continue
            event=json.loads(line[6:]); event_record={'elapsed_seconds':received-t0,'unix':time.time(),'event':event}
            f.write(json.dumps(event_record)+'\n'); events.append(event_record)
            if event.get('stop'): final=event
            if STOP.is_set(): raise InterruptedError('stop during inference')
    if final is None: raise RuntimeError('SSE closed without final response')
    arrival=[]
    for e in events:
        if not e['event'].get('stop'):
            arrival.extend([e['elapsed_seconds']]*len(e['event'].get('tokens',[])))
    itls=[b-a for a,b in zip(arrival,arrival[1:])]
    batches=[len(e['event'].get('tokens',[])) for e in events if not e['event'].get('stop')]
    return {'request_start_unix':start_unix,'request_end_unix':time.time(),'request_wall_seconds':time.monotonic()-t0,'ttft_seconds':arrival[0] if arrival else None,'inter_token_arrivals_seconds':itls,'itl_mean_seconds':statistics.mean(itls) if itls else None,'itl_median_seconds':statistics.median(itls) if itls else None,'stream_token_count':len(arrival),'stream_event_batch_sizes':batches,'arrival_metric_definition':'client receipt times of SSE token events; multi-token events share receipt time; includes transport/serialization/client logging, not internal per-token latency','final':final}

def sample_rss(pid, stop, path):
    # ps reports RSS in KiB on macOS. Sampled peak differs from OS lifetime peak.
    with open(path,'w',buffering=1) as f:
        while not stop.is_set():
            result=cmd(['/bin/ps','-o','rss=,%cpu=','-p',str(pid)])
            fields=result['stdout'].split()
            if len(fields)==2:
                f.write(json.dumps({'unix':time.time(),'rss_kib':int(fields[0]),'process_cpu_percent':float(fields[1])})+'\n')
            stop.wait(1)

def terminate(proc):
    if proc and proc.poll() is None:
        proc.terminate()
        try: proc.wait(timeout=10)
        except subprocess.TimeoutExpired: proc.kill();proc.wait()

def close_server():
    proc=SERVER.get('proc')
    if proc:
        for pid in cmd(['/usr/bin/pgrep','-P',str(proc.pid)])['stdout'].split():
            try: os.kill(int(pid),signal.SIGTERM)
            except ProcessLookupError: pass
        try: proc.wait(timeout=15)
        except subprocess.TimeoutExpired: terminate(proc)
        SERVER['stderr'].close()
    SERVER.clear()

def run_one(session, task, study, models, sensor, baseline, earliest):
    existing=list((session/'runs').glob(task['id']+'-attempt*/result.json'))
    for path in existing:
        previous=json.loads(path.read_text())
        if previous.get('status')=='ok': return previous
    attempt=len(list((session/'runs').glob(task['id']+'-attempt*')))+1
    folder=session/'runs'/(task['id']+f'-attempt{attempt}')
    folder.mkdir(parents=True)
    record={'schema_version':1,'run_id':folder.name,'task':task,'status':'starting','created_at':utc(),'study_sha256':sha(session/'study.json'),'model':models[task['model_id']]}
    save(folder/'state.json',record)
    proc=None;monitor_stop=threading.Event();monitor_thread=None
    try:
        gate=thermal(sensor,baseline,study,folder/'thermal-gate.json',earliest)
        record['thermal_gate']=gate
        model=models[task['model_id']]
        args=[str(BIN/'llama-server'),'-m',str(MODEL_DIR/model['filename']),'-c',str(study['context_capacity']),'-t',str(study['threads']),'-tb',str(study['threads']),'-b',str(study['batch']),'-ub',str(study['ubatch']),'-ngl','0','-np','1','-fa','on','-ctk',task['cache_type'],'-ctv',task['cache_type'],'--host','127.0.0.1','--port','8088','--no-webui']
        record['server_command']=args
        record['thread_environment']={'VECLIB_MAXIMUM_THREADS':'4','OMP_NUM_THREADS':'4'}
        record['power_before']=cmd(['/usr/bin/pmset','-g','batt'])
        record['vm_before']=cmd(['/usr/bin/vm_stat'])
        record['swap_before']=cmd(['/usr/sbin/sysctl','vm.swapusage'])
        record['background_before']=cmd(['/bin/ps','-Ao','pid,pcpu,comm'])
        # /usr/bin/time captures OS process-lifetime maximum RSS after exit;
        # request-only sampled memory is available separately below.
        key=(task['model_id'],task['input_tokens'],task['output_tokens'],task['cache_type'])
        reused=SERVER.get('key')==key and SERVER['proc'].poll() is None
        if not reused:
            close_server()
            stderr=open(folder/'server.txt','w')
            load_t0=time.monotonic()
            proc=subprocess.Popen(['/usr/bin/time','-l']+args,stdout=stderr,stderr=stderr,env=dict(os.environ,**record['thread_environment']))
            SERVER.update(proc=proc,stderr=stderr,key=key,log=str((folder/'server.txt').relative_to(session)))
            for _ in range(900):
                if proc.poll() is not None: raise RuntimeError('server exited while loading')
                try:
                    with urllib.request.urlopen(BASE+'/health',timeout=1) as r:
                        if r.status==200: break
                except Exception: time.sleep(.1)
            else: raise RuntimeError('server did not become ready')
            record['startup_ready_seconds']=time.monotonic()-load_t0
            children=cmd(['/usr/bin/pgrep','-P',str(proc.pid)])['stdout'].split()
            SERVER['pid']=int(children[0]) if children else proc.pid
        else:
            proc=SERVER['proc'];record['startup_ready_seconds']=None
        server_pid=SERVER['pid'];record['server_log']=SERVER['log'];record['same_process_reused']=reused
        record['server_pid']=server_pid
        p=prompt(task['input_tokens'],folder/'prompt.json',session/'corpus-v1.txt')
        request={'prompt':p['tokens'],'n_predict':task['output_tokens'],'temperature':0,'seed':113,'ignore_eos':True,'cache_prompt':False,'stream':True,'return_tokens':True,'timings_per_token':False}
        save(folder/'request.json',request)
        if not reused and task['phase'] in ('main','kv','overhead'):
            # Resume within a block loses the process warm state. Repeat a full
            # warm-up in the new process, preserve evidence, then cool/gap again.
            warm=stream(request,folder/'auxiliary-warmup-stream.jsonl')
            save(folder/'auxiliary-warmup.json',warm)
            earliest=max(earliest,warm['request_end_unix']+study['minimum_repeat_gap_seconds'])
        record['request_thermal_gate']=thermal(sensor,baseline,study,folder/'request-thermal-gate.json',earliest)
        if task.get('instrumentation',True):
            monitor_thread=threading.Thread(target=sample_rss,args=(server_pid,monitor_stop,folder/'memory.jsonl'),daemon=True);monitor_thread.start()
        record['started_at']=utc();save(folder/'state.json',record)
        measured=stream(request,folder/'stream.jsonl')
        record.update(measured)
        final=measured['final'];timings=final['timings']
        record['runtime_timings']=timings
        record['input_tokens_actual']=final['tokens_evaluated']
        record['output_tokens_actual']=final['tokens_predicted']
        record['stop_type']=final.get('stop_type')
        record['context_truncated']=final.get('truncated')
        if final['tokens_evaluated']!=task['input_tokens']: raise RuntimeError('actual prompt count mismatch')
        if final['tokens_predicted']!=task['output_tokens']: raise RuntimeError('actual generation count mismatch')
        if measured['stream_token_count']!=task['output_tokens']: raise RuntimeError('SSE token arrival count mismatch')
        if final.get('truncated'): raise RuntimeError('unexpected context truncation')
        if timings.get('cache_n',0): raise RuntimeError('unexpected prompt cache reuse')
        record['status']='ok'
    except BaseException as exc:
        record['status']='interrupted' if isinstance(exc,(KeyboardInterrupt,InterruptedError)) else 'failed'
        record['error']={'type':type(exc).__name__,'message':str(exc)}
        log(f"{task['id']}: {record['status']}: {exc}")
    finally:
        monitor_stop.set()
        if monitor_thread: monitor_thread.join(timeout=5)
        if record['status']!='ok': close_server()
        record['finished_at']=utc()
        record['power_after']=cmd(['/usr/bin/pmset','-g','batt'])
        record['vm_after']=cmd(['/usr/bin/vm_stat'])
        if (folder/'memory.jsonl').exists():
            mem=[json.loads(x)['rss_kib'] for x in (folder/'memory.jsonl').read_text().splitlines()]
            record['sampled_peak_rss_kib']=max(mem) if mem else None
        save(folder/'result.json',record)
        with open(session/'summary.jsonl','a') as f: f.write(json.dumps(record)+'\n')
    return record

def plan(study):
    configs=[{'model_id':m,'input_tokens':i,'output_tokens':o,'cache_type':'f16'} for m in ['qwen05_q4','qwen05_q8','qwen15_q4','qwen15_q8'] for i in study['input_tokens'] for o in study['output_tokens']]
    tasks=[]
    # Pilot is deliberately repeated before the headline sweep. Both exceed the
    # original 128-output pilot by exercising the adopted largest 512-output case.
    largest={'model_id':'qwen15_q8','input_tokens':2048,'output_tokens':512,'cache_type':'f16'}
    for rep in range(2): tasks.append(dict(largest,id=f'pilot-largest-{rep}',phase='pilot',repetition=rep))
    # Paired alternating order isolates the incremental 1 Hz RSS sampler. The
    # continuously running temperature/power collectors are common to both arms;
    # this is not an estimate of the cost of every instrumentation component.
    for rep in range(3):
        for monitored in ([False,True] if rep%2==0 else [True,False]):
            tasks.append({'model_id':'qwen05_q4','input_tokens':256,'output_tokens':128,'cache_type':'f16','id':f'overhead-pair{rep}-rss{int(monitored)}','phase':'overhead','repetition':rep,'instrumentation':monitored})
    rng=random.Random(study['random_seed'])
    shuffled=configs.copy();rng.shuffle(shuffled)
    for block,cfg in enumerate(shuffled):
        key=f"{cfg['model_id']}-i{cfg['input_tokens']}-o{cfg['output_tokens']}-f16"
        tasks.append(dict(cfg,id=key+'-warmup',phase='warmup',repetition=0,randomized_block=block))
        for rep in range(1,study['repetitions']+1):
            tasks.append(dict(cfg,id=key+f'-r{rep}',phase='main',repetition=rep))
    for rep in range(4):
        tasks.append({'model_id':'qwen15_q4','input_tokens':2048,'output_tokens':128,'cache_type':'q8_0','id':f'kv-q8-r{rep}','phase':'kv_warmup' if rep==0 else 'kv','repetition':rep})
    return tasks

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--session',default='mac-20261113-cpu-v1');ap.add_argument('--limit',type=int);ap.add_argument('--prepare-only',action='store_true');args=ap.parse_args()
    session=ROOT/'results'/args.session;session.mkdir(parents=True,exist_ok=True);(session/'runs').mkdir(exist_ok=True)
    lock=open(ROOT/'results/study.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    study=json.loads((ROOT/'configs/study.json').read_text());models={m['id']:m for m in json.loads((ROOT/'configs/models.json').read_text())}
    if not (session/'study.json').exists():
        save(session/'study.json',study);save(session/'models.json',list(models.values()));save(session/'plan.json',plan(study))
        inventory={'captured_at':utc(),'python':sys.version,'source_commit_expected':COMMIT,'source_archive_sha256':sha(RUNTIME.parent/'llama-b6784.tar.gz'),'binary_sha256':sha(BIN/'llama-server'),'cmake_cache':(RUNTIME/'build-cpu/CMakeCache.txt').read_text(),'system':cmd(['/usr/bin/sw_vers']),'sysctl':cmd(['/usr/sbin/sysctl','hw.model','hw.memsize','hw.ncpu','hw.physicalcpu','hw.logicalcpu']),'power':cmd(['/usr/bin/pmset','-g','batt']),'macmon_version':cmd(['/opt/homebrew/bin/macmon','--version']),'model_checksums':{m['id']:sha(MODEL_DIR/m['filename']) for m in models.values()}}
        for model in models.values():
            if inventory['model_checksums'][model['id']]!=model['sha256']: raise RuntimeError('model checksum mismatch')
        save(session/'inventory.json',inventory)
    else:
        if json.loads((session/'study.json').read_text())!=study: raise RuntimeError('study changed; create a new session')
    frozen=session/'provenance.json'
    actual={'harness_sha256':sha(Path(__file__)),'binary_sha256':sha(BIN/'llama-server'),'model_manifest_sha256':sha(ROOT/'configs/models.json'),'corpus_sha256':sha(ROOT/'prompts/corpus-v1.txt'),'study_sha256':sha(ROOT/'configs/study.json'),'plan_sha256':sha(session/'plan.json')}
    if not frozen.exists():
        (session/'corpus-v1.txt').write_bytes((ROOT/'prompts/corpus-v1.txt').read_bytes())
        (session/'harness.py').write_bytes(Path(__file__).read_bytes())
        save(frozen,actual)
    elif json.loads(frozen.read_text())!=actual:
        raise RuntimeError('harness/binary/corpus/manifest/plan changed; use original snapshot or create a new session')
    if json.loads((session/'models.json').read_text())!=list(models.values()): raise RuntimeError('model manifest changed')
    study=json.loads((session/'study.json').read_text());models={m['id']:m for m in json.loads((session/'models.json').read_text())}
    for m in models.values():
        if sha(MODEL_DIR/m['filename'])!=m['sha256']: raise RuntimeError('model bytes changed: '+m['id'])
    if args.prepare_only: return
    if cmd(['/usr/sbin/lsof','-tiTCP:8088','-sTCP:LISTEN'])['stdout'].strip(): raise RuntimeError('port8088 already in use; identify stale server before resuming')
    sensor=Sensor(session/('sensors-'+dt.datetime.now().strftime('%Y%m%dT%H%M%S')+'.jsonl'));sensor.start()
    try:
        baseline_path=session/'idle-baseline.json'
        if baseline_path.exists(): baseline=json.loads(baseline_path.read_text())['mean']
        else:
            log('Waiting for stable 60-second idle baseline')
            observed=thermal(sensor,None,study,session/'idle-stabilization.json');baseline=observed['mean'];save(baseline_path,observed)
        log(f'idle baseline: {baseline:.3f} C')
        tasks=json.loads((session/'plan.json').read_text());completed=0
        for task in tasks:
            if STOP.is_set(): break
            previous=[json.loads(p.read_text()) for p in (session/'runs').glob('*/result.json')]
            if any(x.get('status')=='ok' and x['task']['id']==task['id'] for x in previous): continue
            related=[x.get('request_end_unix',0) for x in previous if x['task']['model_id']==task['model_id'] and x['task']['input_tokens']==task['input_tokens'] and x['task']['output_tokens']==task['output_tokens'] and x['task']['cache_type']==task['cache_type']]
            earliest=max(related,default=0)+study['minimum_repeat_gap_seconds']
            log('Starting '+task['id'])
            result=run_one(session,task,study,models,sensor,baseline,earliest)
            if result['status']!='ok':
                # A failed pilot blocks feasibility-dependent headline claims.
                if task['phase']=='pilot': raise RuntimeError('pilot failed; inspect raw evidence before sweep')
            else: log(f"OK {task['id']}: {result['request_wall_seconds']:.2f}s, {result['runtime_timings']['predicted_per_second']:.2f}decode tok/s")
            completed+=1
            save(session/'progress.json',{'updated_at':utc(),'last_run_id':result['run_id'],'last_status':result['status'],'successful':sum(x.get('status')=='ok' for x in previous)+(result['status']=='ok'),'planned':len(tasks),'pid':os.getpid()})
            if args.limit and completed>=args.limit: break
    finally: close_server();sensor.stop()

if __name__=='__main__':
    def handle(sig,frame): STOP.set()
    signal.signal(signal.SIGINT,handle);signal.signal(signal.SIGTERM,handle)
    main()
