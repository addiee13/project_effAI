#!/usr/bin/env python3
"""Validate raw session records and create traceable descriptive tables/plots."""
import argparse, csv, json, math, statistics, sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]

def load_sensor(path):
    out=[]
    for line in path.read_text().splitlines():
        try: out.append(json.loads(line))
        except json.JSONDecodeError: continue
    return out

def during(samples,start,end,field):
    pairs=[]
    for sample in samples:
        t=sample.get('received_unix')
        if t is None or not start<=t<=end: continue
        value=sample
        for part in field.split('.'):
            value=value.get(part) if isinstance(value,dict) else None
        if isinstance(value,(int,float)) and math.isfinite(value): pairs.append((t,float(value)))
    return pairs

def integrate_component(samples,start,end):
    # Integrate only when samples bracket the full request and the cadence has
    # no gaps above 3 s. Values are macmon estimated CPU/GPU/ANE watts.
    rows=[]
    for s in samples:
        t=s.get('received_unix')
        vals=[s.get(k) for k in ('cpu_power','gpu_power','ane_power')]
        if t is not None and all(isinstance(x,(int,float)) for x in vals): rows.append((t,sum(vals)))
    rows.sort()
    left=max((i for i,r in enumerate(rows) if r[0]<=start),default=None)
    right=min((i for i,r in enumerate(rows) if r[0]>=end),default=None)
    if left is None or right is None: return None
    selected=rows[left:right+1]
    if len(selected)<2 or selected[0][0]>start or selected[-1][0]<end or any(b[0]-a[0]>3 for a,b in zip(selected,selected[1:])): return None
    clipped=[]
    for a,b in zip(selected,selected[1:]):
        if b[0]<start or a[0]>end: continue
        t0=max(a[0],start);t1=min(b[0],end)
        if t1<=t0: continue
        def interp(t): return a[1]+(b[1]-a[1])*(t-a[0])/(b[0]-a[0])
        clipped.append((t0,interp(t0)));clipped.append((t1,interp(t1)))
    # Merge duplicate boundary points before trapezoidal integration.
    compact=[]
    for r in clipped:
        if compact and compact[-1][0]==r[0]: compact[-1]=r
        else: compact.append(r)
    if len(compact)<2 or compact[0][0]>start+1 or compact[-1][0]<end-1: return None
    return sum((b[0]-a[0])*(a[1]+b[1])/2 for a,b in zip(compact,compact[1:]))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--session',required=True);args=ap.parse_args()
    session=ROOT/'results'/args.session
    if not (session/'provenance.json').exists(): raise SystemExit('session lacks frozen provenance')
    manifest=json.loads((session/'models.json').read_text());models={m['id']:m for m in manifest}
    plan=json.loads((session/'plan.json').read_text());expected={t['id']:t for t in plan if t['phase']=='main'}
    paths=sorted((session/'runs').glob('*/result.json'));records=[];issues=[]
    sensor_paths=sorted(session.glob('sensors-*.jsonl'))
    sensor_cache={p.name:load_sensor(p) for p in sensor_paths}
    for path in paths:
        r=json.loads(path.read_text()); task=r.get('task',{})
        if task.get('phase')!='main': continue
        reasons=[]
        if r.get('status')!='ok': reasons.append('status_not_ok')
        if task.get('id') not in expected: reasons.append('not_in_frozen_plan')
        if r.get('input_tokens_actual')!=task.get('input_tokens'): reasons.append('input_count_mismatch')
        if r.get('output_tokens_actual')!=task.get('output_tokens'): reasons.append('output_count_mismatch')
        if r.get('context_truncated'): reasons.append('truncated')
        if r.get('runtime_timings',{}).get('cache_n')!=0: reasons.append('prompt_cache_reuse')
        if r.get('stream_token_count')!=task.get('output_tokens'): reasons.append('stream_count_mismatch')
        if r.get('stop_type')!='limit': reasons.append('unexpected_stop_type')
        if reasons: issues.append({'run_id':r.get('run_id',path.parent.name),'reasons':reasons});continue
        sensor=sensor_cache.get(r.get('sensor_log'),[])
        start=r['request_start_unix'];end=r['request_end_unix']
        temps=during(sensor,start,end,'temp.cpu_temp_avg')
        cpu=during(sensor,start,end,'cpu_power');gpu=during(sensor,start,end,'gpu_power');ane=during(sensor,start,end,'ane_power')
        task_model=models[task['model_id']]
        quant='Q4_K_M' if 'q4_k_m' in task_model['filename'].lower() else 'Q8_0'
        rows={'run_id':r.get('run_id',path.parent.name),'record_path':str(path.relative_to(ROOT)),'model_id':task['model_id'],'model':task_model['checkpoint'],'weight_quant':quant,'input_tokens':task['input_tokens'],'output_tokens':task['output_tokens'],'cache_type':task['cache_type'],'n':1,'request_start_unix':start,'request_end_unix':end,'input_tokens_actual':r['input_tokens_actual'],'output_tokens_actual':r['output_tokens_actual'],'stop_type':r['stop_type'],'runtime_prompt_s':r['runtime_timings']['prompt_ms']/1000,'prefill_tokens_per_s':r['runtime_timings']['prompt_per_second'],'runtime_decode_s':r['runtime_timings']['predicted_ms']/1000,'decode_tokens_per_s':r['runtime_timings']['predicted_per_second'],'request_wall_s':r['request_wall_seconds'],'ttft_arrival_proxy_s':r['ttft_seconds'],'itl_arrival_proxy_median_s':r.get('itl_median_seconds'),'sampled_peak_rss_mib':r['sampled_peak_rss_kib']/1024 if r.get('sampled_peak_rss_kib') is not None else None,'cpu_temp_mean_c':statistics.mean(x[1] for x in temps) if temps else None,'cpu_temp_min_c':min((x[1] for x in temps),default=None),'cpu_temp_max_c':max((x[1] for x in temps),default=None),'cpu_power_mean_w':statistics.mean(x[1] for x in cpu) if cpu else None,'gpu_power_mean_w':statistics.mean(x[1] for x in gpu) if gpu else None,'ane_power_mean_w':statistics.mean(x[1] for x in ane) if ane else None,'estimated_component_request_j':integrate_component(sensor,start,end),'sensor_log':r.get('sensor_log')}
        rows['thermal_window_range_c']=((r.get('thermal_gate') or {}).get('maximum',0)-(r.get('thermal_gate') or {}).get('minimum',0)) if (r.get('thermal_gate') or {}).get('minimum') is not None else None
        rows['thermal_gate_accepted']=bool((r.get('thermal_gate') or {}).get('accepted',False))
        rows['thermal_gate_timed_out']=bool((r.get('thermal_gate') or {}).get('timeout_expired',False))
        records.append(rows)
    missing=sorted(set(expected)-{r['run_id'].removesuffix('-attempt1') for r in records})
    # Planned IDs and result IDs are intentionally separate; calculate exact coverage by task ID.
    successful_tasks={json.loads(p.read_text()).get('task',{}).get('id') for p in paths if json.loads(p.read_text()).get('status')=='ok' and json.loads(p.read_text()).get('task',{}).get('phase')=='main' and json.loads(p.read_text()).get('input_tokens_actual')==json.loads(p.read_text()).get('task',{}).get('input_tokens') and json.loads(p.read_text()).get('output_tokens_actual')==json.loads(p.read_text()).get('task',{}).get('output_tokens') and json.loads(p.read_text()).get('stop_type')=='limit' and not json.loads(p.read_text()).get('context_truncated') and json.loads(p.read_text()).get('runtime_timings',{}).get('cache_n')==0}
    missing=sorted(set(expected)-successful_tasks)
    out=ROOT/'analysis'/args.session;out.mkdir(parents=True,exist_ok=True)
    (out/'validated_runs.json').write_text(json.dumps(records,indent=2)+'\n')
    (out/'audit.json').write_text(json.dumps({'session':args.session,'planned_main_configurations':len(expected),'validated_unique_configurations':len(successful_tasks),'missing_or_invalid_configurations':missing,'invalid_records':issues,'aggregation':'one point per configuration; no mean, SD, confidence interval, or significance is reported for n=1','source_run_paths':[r['record_path'] for r in records]},indent=2)+'\n')
    if records:
        with open(out/'validated_runs.csv','w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
        fig,axes=plt.subplots(2,2,figsize=(12,8),sharex=True)
        for row,output in enumerate([128,512]):
            for col,model_id in enumerate(['qwen05','qwen15']):
                ax=axes[row,col]
                for quant,marker in [('Q4_K_M','o'),('Q8_0','s')]:
                    subset=[x for x in records if x['model_id'].startswith(model_id) and x['output_tokens']==output and x['weight_quant']==quant]
                    subset.sort(key=lambda x:x['input_tokens'])
                    if subset: ax.plot([x['input_tokens'] for x in subset],[x['decode_tokens_per_s'] for x in subset],marker=marker,linewidth=2,label=quant)
                ax.set_title(f'{"0.5B" if model_id=="qwen05" else "1.5B"} · {output} generated tokens')
                ax.set_ylabel('Runtime decode tokens/s');ax.set_xlabel('Actual input tokens');ax.grid(alpha=.25);ax.legend()
        fig.suptitle('Mac CPU presentation pilot: one observation per configuration (n=1)');fig.tight_layout()
        fig.savefig(out/'decode_throughput.png',dpi=180,bbox_inches='tight');plt.close(fig)
        fig,axes=plt.subplots(1,2,figsize=(12,4.8))
        for ax,metric,label in [(axes[0],'request_wall_s','Request wall time (s)'),(axes[1],'sampled_peak_rss_mib','Sampled peak process RSS (MiB)')]:
            for model_id,ls in [('qwen05','-'),('qwen15','--')]:
                for quant,marker in [('Q4_K_M','o'),('Q8_0','s')]:
                    subset=[x for x in records if x['model_id'].startswith(model_id) and x['output_tokens']==512 and x['weight_quant']==quant and x[metric] is not None]
                    subset.sort(key=lambda x:x['input_tokens'])
                    if subset: ax.plot([x['input_tokens'] for x in subset],[x[metric] for x in subset],linestyle=ls,marker=marker,label=f'{"0.5B" if model_id=="qwen05" else "1.5B"} {quant}')
            ax.set_xlabel('Actual input tokens');ax.set_ylabel(label);ax.grid(alpha=.25)
            if ax is axes[1]: ax.legend(fontsize=8,loc='upper left',bbox_to_anchor=(1.02,1))
            else: ax.legend(fontsize=8)
        fig.suptitle('Mac CPU pilot at 512 generated tokens (n=1 per point)');fig.tight_layout(rect=(0,0,.82,1))
        fig.savefig(out/'request_memory.png',dpi=180,bbox_inches='tight');plt.close(fig)
        fig,axes=plt.subplots(1,2,figsize=(12.5,4.4),sharey=True)
        for ax,model_id,title in [(axes[0],'qwen05','Qwen2.5 0.5B'),(axes[1],'qwen15','Qwen2.5 1.5B')]:
            for quant,marker in [('Q4_K_M','o'),('Q8_0','s')]:
                subset=[x for x in records if x['model_id'].startswith(model_id) and x['output_tokens']==512 and x['weight_quant']==quant and x['estimated_component_request_j'] is not None]
                subset.sort(key=lambda x:x['input_tokens'])
                if subset: ax.plot([x['input_tokens'] for x in subset],[x['estimated_component_request_j'] for x in subset],marker=marker,linewidth=2,label=quant)
            ax.set_title(title);ax.set_xlabel('Actual input tokens');ax.grid(alpha=.25);ax.legend()
        axes[0].set_ylabel('Estimated CPU + GPU + ANE request energy (J)',fontsize=12)
        for ax in axes:
            ax.tick_params(labelsize=10);ax.xaxis.label.set_size(11);ax.title.set_size(13)
        fig.suptitle('Gross component-rail estimate; 11 of 12 points available, n=1');fig.tight_layout()
        fig.savefig(out/'component_request_energy.png',dpi=180,bbox_inches='tight');plt.close(fig)
    print(json.dumps({'planned':len(expected),'validated':len(successful_tasks),'invalid_records':len(issues),'missing':missing,'output':str(out.relative_to(ROOT))},indent=2))
    if issues or missing: sys.exit(2)

if __name__=='__main__':main()
