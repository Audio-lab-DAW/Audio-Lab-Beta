import sys,json
from playwright.sync_api import sync_playwright
A=open('wl.js').read();B=open('wl3.js').read()
names=['al-imager']
JS="""async([wl,nm])=>{const sr=48000,T=8,c=new OfflineAudioContext(2,sr*T,sr);await c.audioWorklet.addModule(URL.createObjectURL(new Blob([wl],{type:'text/javascript'})));
const b=c.createBuffer(2,sr*T,sr);let s=12345;const rnd=()=>{s=(s*1664525+1013904223)>>>0;return s/2147483648-1};for(let ch=0;ch<2;ch++){const d=b.getChannelData(ch);for(let i=0;i<sr*T;i++){const t=i/sr;d[i]=(t<1||(t>5&&t<6))?rnd()*.5:(t>6.5&&t<7?rnd()*1e-4:0)}}
const src=c.createBufferSource();src.buffer=b;const n=new AudioWorkletNode(c,nm,{numberOfInputs:1,numberOfOutputs:1,outputChannelCount:[2],processorOptions:{p:{}}});src.connect(n);n.connect(c.destination);src.start();
const r=await c.startRendering();return [Array.from(r.getChannelData(0)),Array.from(r.getChannelData(1))]}"""
import numpy as np
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page()
    pg.route('https://app.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body='<html></html>'))
    pg.goto('https://app.test/index.html')
    for nm in names:
        x=np.array(pg.evaluate(JS,[A,nm]));y=np.array(pg.evaluate(JS,[B,nm]));x2=np.array(pg.evaluate(JS,[A,nm]))
        d=np.abs(x-y).max();d0=np.abs(x-x2).max()
        print(nm.ljust(10),'peak %.3f'%np.abs(x).max(),'old-vs-new diff',d,'| old-vs-old',d0,flush=True)
    b.close()
