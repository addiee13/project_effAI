#!/usr/bin/env python3
"""Build evidence-aware PDFs from editable Markdown/JSON. No inference is launched."""
from pathlib import Path
import argparse, hashlib, json, re, html
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

BASE=Path(__file__).resolve().parents[1]
SRC=BASE/'source'; OUT=BASE/'output'; VALID=BASE/'validation'
INK=colors.HexColor('#142E3A'); TEAL=colors.HexColor('#007D82'); GRAY=colors.HexColor('#4B606A'); PAPER=colors.HexColor('#F7F6F1'); ORANGE=colors.HexColor('#BD652E')
FONT_DIR=Path('/System/Library/Fonts/Supplemental')
for name,file in [('Body','Arial.ttf'),('Bold','Arial Bold.ttf'),('Italic','Arial Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT_DIR/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Italic',boldItalic='Bold')

def fmt(text):
    text=html.escape(text)
    text=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'(https?://[^\s<>]+)',r'<link href="\1" color="#007D82">\1</link>',text)
    return text

def para(c,text,x,y,width,size=10.3,leading=14.8,color=INK,font='Body',gap=10):
    p=Paragraph(fmt(text),ParagraphStyle('p',fontName=font,fontSize=size,leading=leading,textColor=color,splitLongWords=True))
    w,h=p.wrap(width,10000)
    p.drawOn(c,x,y-h)
    return y-h-gap

def footer(c,num,label):
    c.setStrokeColor(colors.HexColor('#D3DEDF')); c.line(52,43,560,43)
    c.setFont('Body',8); c.setFillColor(GRAY); c.drawString(52,29,label); c.drawRightString(560,29,str(num))

def report(snapshot):
    raw=(SRC/'report.md').read_text()
    for k in ['results_overview','results_detail','conclusion_evidence']:
        raw=raw.replace('{{'+k.upper()+'}}',snapshot[k])
    (OUT/'report_rendered.md').write_text(raw)
    pages=raw.split('---PAGE---')
    c=canvas.Canvas(str(OUT/'effai_report.pdf'),pagesize=(612,792)); c.setTitle('Efficiency Profiling of Small Language Models on Edge Hardware'); c.setAuthor('Adam Dalwai, Mahean Seam, Vrushti Patel')
    sizes=[]
    for n,page in enumerate(pages,1):
        c.setFillColor(PAPER); c.rect(0,0,612,792,fill=1,stroke=0)
        c.setFillColor(TEAL); c.rect(0,773,612,19,fill=1,stroke=0)
        y=749
        for block in page.strip().split('\n\n'):
            lines=block.strip().split('\n')
            for line in lines:
                if line.startswith('# '):
                    y=para(c,line[2:],52,y,508,size=22,leading=27,font='Bold',gap=13)
                elif line.startswith('## '):
                    y=para(c,line[3:],52,y,508,size=18,leading=22,font='Bold',gap=16)
                elif line.strip():
                    y=para(c,line,52,y,508)
        if y<55:
            raise ValueError(f'Report page {n} content overflow: {y:.1f}; edit content or layout before delivery')
        sizes.append({'page':n,'words':len(page.split()),'bottom_y':round(y,1)})
        footer(c,n,'EFFAI | Mac phase · Android pending | evidence snapshot '+snapshot.get('status','unknown'))
        c.showPage()
    # Add measured-data figures as appendices, preserving main text page count.
    for file in snapshot.get('figures',[]):
        path=BASE/file['path']
        if not path.exists(): raise FileNotFoundError(path)
        n+=1; c.setFillColor(PAPER);c.rect(0,0,612,792,fill=1,stroke=0)
        y=para(c,file['title'],52,740,508,size=18,leading=23,font='Bold')
        from PIL import Image
        with Image.open(path) as im: iw,ih=im.size
        dw=508; dh=dw*ih/iw
        if dh>475: dh=475;dw=dh*iw/ih
        c.drawImage(str(path),52,y-dh-12,width=dw,height=dh)
        para(c,file.get('caption',''),52,y-dh-28,508,size=10,leading=14)
        footer(c,n,'EFFAI | Measured evidence appendix');c.showPage()
    c.save(); return sizes

def resolved_slides(snapshot):
    data=json.loads((SRC/'slides.json').read_text())
    mapping={'coverage_line':snapshot.get('coverage_line','Main matrix: awaiting validated evidence'), 'decode_line':snapshot.get('decode_line','Decode comparison pending validated measurements'), 'context_line':snapshot.get('context_line','Context comparison pending validated measurements'),'energy_line':snapshot.get('energy_line','Request-boundary component energy pending validated measurements')}
    for s in data['slides']:
        s['points']=[re.sub(r'\{\{(.*?)\}\}',lambda m:mapping[m[1]],p) for p in s['points']]
    return data

def deck(snapshot):
    data=resolved_slides(snapshot)
    c=canvas.Canvas(str(OUT/'effai_slides.pdf'),pagesize=(960,540)); c.setTitle(data['title']); c.setAuthor(data['authors'])
    notes=['# Speaker notes and rehearsal plan','', 'Target: 18:00 including the 1:30 evidence demo. Timing is a rehearsal budget, not measured delivery.','']
    elapsed=0; sizes=[]
    for n,s in enumerate(data['slides'],1):
        c.setFillColor(PAPER);c.rect(0,0,960,540,fill=1,stroke=0)
        c.setFillColor(TEAL);c.rect(0,0,16,540,fill=1,stroke=0)
        c.setFont('Bold',12);c.setFillColor(TEAL);c.drawString(58,493,'EFFICIENCY PROFILING / QWEN2.5')
        y=para(c,s['title'],58,462,844,size=31,leading=37,font='Bold',gap=25)
        if s['layout']=='title':
            y=para(c,data['subtitle'],58,y,820,size=19,leading=26,color=GRAY,gap=20)
        fig_key={'results_decode':'decode','results_context':'context','energy':'energy'}.get(s['layout'])
        figure=next((f for f in snapshot.get('figures',[]) if f.get('key')==fig_key),None) if fig_key else None
        if figure:
            if s['layout']=='energy':
                c.drawImage(str(BASE/figure['path']),55,120,width=840,height=300,preserveAspectRatio=True,anchor='c')
                para(c,s['points'][0],60,103,840,size=13,leading=16,gap=0)
                para(c,'; '.join(s['points'][1:]),60,82,840,size=12,leading=15,gap=0)
                y=65
            else:
                c.drawImage(str(BASE/figure['path']),55,112,width=540,height=260,preserveAspectRatio=True,anchor='c')
                for point in s['points']:
                    y=para(c,point,625,y,275,size=18,leading=25,gap=22)
        elif s['layout']=='phases':
            labels=['LOAD','PREFILL','DECODE','DELIVERY']
            for j,label in enumerate(labels):
                x=58+j*212;c.setFillColor(TEAL if j<3 else INK);c.rect(x,252,194,66,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('Bold',18);c.drawCentredString(x+97,276,label)
                para(c,s['points'][j].split(': ',1)[1],x,232,194,size=17,leading=23,color=GRAY)
            y=120
        else:
            for j,point in enumerate(s['points']):
                c.setFillColor(ORANGE);c.circle(64,y-12,3.5,fill=1,stroke=0)
                y=para(c,point,82,y,800,size=23 if len(point)<76 else 21,leading=30,gap=22)
        if y<58: raise ValueError(f'Slide {n} overflow at {y}')
        c.setStrokeColor(colors.HexColor('#C7D6D7'));c.line(58,54,904,54)
        c.setFont('Body',9);c.setFillColor(GRAY);c.drawString(58,33,'Mac CPU phase | Android pending' if n!=17 else 'Full URLs and provenance in report + editable source');c.drawRightString(904,33,f'{n:02d} / {len(data["slides"]):02d}')
        c.showPage()
        notes += [f'## {n}. {s["title"]}',f'Budget: {s["seconds"]} s | {elapsed//60:02d}:{elapsed%60:02d} to {(elapsed+s["seconds"])//60:02d}:{(elapsed+s["seconds"])%60:02d}', '',s['notes'],'']
        elapsed+=s['seconds'];sizes.append({'slide':n,'seconds':s['seconds'],'bottom_y':y})
    c.save(); (OUT/'speaker_notes.md').write_text('\n'.join(notes));(OUT/'slides_resolved.json').write_text(json.dumps(data,indent=2));return sizes,elapsed

def main():
    OUT.mkdir(exist_ok=True);VALID.mkdir(exist_ok=True)
    snapshot=json.loads((SRC/'results_snapshot.json').read_text())
    rp=report(snapshot);sp,seconds=deck(snapshot)
    validation={'report_pages':len(PdfReader(OUT/'effai_report.pdf').pages),'substantive_pages':12,'report_sections':rp,'slide_pages':len(PdfReader(OUT/'effai_slides.pdf').pages),'presentation_budget_seconds':seconds,'slides':sp,'snapshot_status':snapshot['status'],'snapshot_sha256':hashlib.sha256((SRC/'results_snapshot.json').read_bytes()).hexdigest(),'visual_review':'pending_latest_PNG_inspection'}
    (VALID/'build_manifest.json').write_text(json.dumps(validation,indent=2))
    print(json.dumps({k:v for k,v in validation.items() if k not in ['report_sections','slides']},indent=2))
if __name__=='__main__':main()
