# DR4: builds the pick page from page_src.html: embeds today's screenshots (today_b64.json, made by crops.py) and the colour maps (cmaps.txt).
#   python3 build.py   ->  instruments.html
import json,os
H=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(H,'page_src.html'),encoding='utf-8').read()
today=json.load(open(os.path.join(H,'today_b64.json')))
cm={}
for line in open(os.path.join(H,'cmaps.txt')):
    k,v=line.strip().split('|');cm[k]=v
src=src.replace('/*TODAY*/{}',json.dumps(today)).replace('/*CMAPS*/{}',json.dumps(cm))
open(os.path.join(H,'instruments.html'),'w',encoding='utf-8').write(src)
print('instruments.html',len(src),'bytes')
